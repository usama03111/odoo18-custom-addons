# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TravelRequestRejectReason(models.TransientModel):
    """
    This wizard is used by managers or authorized personnel to input and confirm
    the reason for rejecting a submitted employee travel request. The rejection
    reason is then logged on the corresponding travel request for record-keeping
    and auditing purposes.
    """
    _name = 'travel.request.reject.reason'
    _description = "Travel Request Reject Reason"
    _inherit = ['mail.thread']

    request_reject_reason_id = fields.Many2one(
        'request.reject.reason',
        string="Reject Reason")
    closing_notes = fields.Text(string="Closing Notes")

    def action_travel_request_reject(self):
        """Get the employee travel request reject reason and send mail to employee for travel request is rejected."""
        if self.env.context.get('active_id'):
            record = (self.env['employee.travel.request'].
                      browse(self.env.context.get('active_id')))
            if record:
                record.request_reject_reason = (
                    self.request_reject_reason_id.request_reject_reason)
                closing_notes = self.closing_notes
                record.closing_notes = closing_notes
                record.state = 'rejected'
                record.message_post(
                    body="Travel request has been rejected.",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                template = record.env.ref(
                    'tk_employee_travel_expense.email_template_travel_request_rejected')
                if template:
                    template.send_mail(record.id,
                                       force_send=True,
                                       email_values={"author_id": record.company_id.id})
            return record

    @api.onchange('request_reject_reason_id')
    def _onchange_request_reject_reason_id(self):
        """Automatically update the closing notes based on the selected reason."""
        for record in self:
            record.closing_notes = record.request_reject_reason_id.closing_notes
