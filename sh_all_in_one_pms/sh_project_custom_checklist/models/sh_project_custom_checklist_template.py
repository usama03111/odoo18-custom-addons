# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models

class ProjectCustomChecklistTemplate(models.Model):
    _name = "project.custom.checklist.template"
    _description = "Project Custom Checklist Template"

    name = fields.Char("Name", required=True)
    company_id = fields.Many2one("res.company",
                                 string="Company",
                                 default=lambda self: self.env.company)
    checklist_template_ids = fields.Many2many('project.custom.checklist','checklist_template_ids_rel',
                                              string="Checklist Template")
