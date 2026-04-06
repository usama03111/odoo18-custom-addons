# -*- coding: utf-8 -*-
from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def action_open_manager_evaluation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Manager Evaluations",
            "res_model": "kb.em.evo.form",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {
                "default_employee_id": self.id,
            },
        }
