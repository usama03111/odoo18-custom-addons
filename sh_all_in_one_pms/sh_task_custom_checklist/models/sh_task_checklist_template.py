# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class TaskCustomChecklist(models.Model):
    _name = "sh.task.checklist.template"
    _description = 'Task Checklist Template'
    _order = 'sequence,name, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=1)
    checklist_ids = fields.Many2many("task.custom.checklist",
                                     string="Check List", check_company=True)
    company_id = fields.Many2one("res.company",string="Company",default=lambda self: self.env.company)
