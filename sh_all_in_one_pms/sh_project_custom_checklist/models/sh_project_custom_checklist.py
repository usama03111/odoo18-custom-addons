# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models

class ProjectCustomChecklist(models.Model):
    _name = "project.custom.checklist"
    _description = "Project Custom Checklist"
    _order = "id desc"

    name = fields.Char("Name", required=True)
    description = fields.Char("Description")
    company_id = fields.Many2one("res.company",
                                 string="Company",
                                 default=lambda self: self.env.company)
