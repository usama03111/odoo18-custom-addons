# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api
from datetime import datetime

class ProjectCustomChecklistLine(models.Model):
    _name = "project.custom.checklist.line"
    _description = "Project Custom Checklist Line"
    _order = "id desc"

    name = fields.Many2one("project.custom.checklist", "Name", required=True)
    description = fields.Char("Description")
    updated_date = fields.Date("Date",
                               readonly=True,
                               default=datetime.now().date())
    state = fields.Selection([("new", "New"), ("completed", "Completed"),
                              ("cancelled", "Cancelled")],
                             string="State",
                             default="new",
                             readonly=True,
                             index=True)
    company_id = fields.Many2one("res.company",
                                 string="Company",
                                 default=lambda self: self.env.company)
    project_id = fields.Many2one("project.project")

    def btn_check(self):
        for rec in self:
            rec.write({"state": "completed"})

    def btn_close(self):
        for rec in self:
            rec.write({"state": "cancelled"})

    @api.onchange("name")
    def onchange_custom_chacklist_name(self):
        self.description = self.name.description
