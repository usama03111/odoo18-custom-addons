# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_category_id = fields.Many2one(
        "project.category", string="Project Category")
