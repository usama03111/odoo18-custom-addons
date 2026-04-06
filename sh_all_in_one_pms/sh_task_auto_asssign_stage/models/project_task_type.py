# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    assign_to = fields.Many2one('res.users', "Assign To")
