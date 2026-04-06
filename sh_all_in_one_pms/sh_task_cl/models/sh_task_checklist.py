# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models


class TaskChecklist(models.Model):
    _name = "task.checklist"
    _description = "Task Checklist"

    name = fields.Char(required=True)
    description = fields.Char()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company)
