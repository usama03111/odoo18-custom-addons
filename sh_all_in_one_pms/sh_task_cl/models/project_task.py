# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api


class ProjectTask(models.Model):
    _inherit = "project.task"
    _check_company_auto = True

    checklist_ids = fields.Many2many(
        "task.checklist", string="Checklist")
    checklist = fields.Float(
        "Checklist Completed",
        compute="_compute_checklist", digits=(12, 0))
    state_name = fields.Char("Final State")

    @api.depends("checklist_ids", "state_name")
    def _compute_checklist(self):
        if self:
            for data in self:
                total_cnt = self.env["task.checklist"].search_count(
                    [ ('company_id', "!=", False)])

                comp_cnt = 0
                for rec in data.checklist_ids:
                    if rec.name:
                        if rec.name:
                            comp_cnt += 1

                if total_cnt > 0:
                    data.checklist = (100.0 * comp_cnt) / total_cnt
                    print('cnt--',data.checklist)

                    if data.checklist >= 100:
                        data.state_name = "completed"
                    else:
                        data.state_name = "cancelled"
                else:
                    data.checklist = 0
                    data.state_name = "cancelled"
