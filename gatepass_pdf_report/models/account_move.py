from odoo import models
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_print_gate_pass(self):
        """Trigger Gate Pass PDF report (multi-company restricted)."""
        self.ensure_one()
        if not self.company_id.gatepass_enabled:
            raise UserError("Gate Pass is not enabled for this company.")
        return self.env.ref('gatepass_pdf_report.action_gate_pass_report').report_action(self)
