from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import timedelta
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"


    @api.model
    def _check_overdue_payments_and_send(self):
        """Cron job to check for overdue payments and automatically send notifications"""
        today = fields.Date.today()
        yesterday = fields.Datetime.now() - timedelta(days=1)


        overdue_invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('invoice_date_due', '<', today),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('state', '=', 'posted'),
            ('partner_id.send_overdue_reminder', '=', True),  # ✅ check partner setting
        ])

        # Load the default invoice email template
        template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)

        for invoice in overdue_invoices:
            if template:
                template.send_mail(invoice.id, force_send=True)

        return True

