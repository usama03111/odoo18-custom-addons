from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ManagerEvaluation(models.Model):
    _name = "kb.manager.evaluation"
    _description = "Manager Evaluation Form"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="New", readonly=True, copy=False)
    employee_id = fields.Many2one("hr.employee", required=True)
    manager_id = fields.Many2one("res.users", required=True)
    hr_user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    evaluation_notes = fields.Text(string="Manager Feedback")

    state = fields.Selection([
        ("draft", "Draft"),
        ("sent", "Sent to Manager"),
        ("submitted", "Submitted to HR"),
    ], default="draft", tracking=True)

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("kb.manager.evaluation") or "New"
        return super().create(vals)

    def action_send_to_manager(self):
        for rec in self:
            rec.state = "sent"

    def action_submit_to_hr(self):
        for rec in self:
            if self.env.user != rec.manager_id:
                raise UserError(_("Only the assigned manager can submit this evaluation."))
            rec.state = "submitted"
