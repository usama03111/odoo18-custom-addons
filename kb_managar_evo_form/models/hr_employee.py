from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    manager_evaluation_ids = fields.One2many(
        "hr.employee.manager.evaluation",
        "employee_id",
        string="Manager Evaluations",
    )

    manager_evaluation_count = fields.Integer(
        compute="_compute_manager_eval_count",
        string="Evaluations",
    )

    def _compute_manager_eval_count(self):
        for rec in self:
            rec.manager_evaluation_count = len(rec.manager_evaluation_ids)
