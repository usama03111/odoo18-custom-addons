# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TaskApprovalConfig(models.Model):
    _name = 'sh.task.approval.config'
    _description = 'Task Approval Configuration'

    name = fields.Char(string="Name", required=True)
    project_ids = fields.Many2many('project.project', string="Applicable Projects")
    stage_ids = fields.Many2many('project.task.type', string="Applicable Stages")
    company_ids = fields.Many2many(
        'res.company', string="Allowed Companies", default=lambda self: self.env.company)
    task_approval_line = fields.One2many('sh.task.approval.config.line', 'task_approval_config_id', 
                                       string='Task approval line')

    @api.constrains('task_approval_line')
    def approval_line_level(self):
        if self.task_approval_line:
            levels = self.task_approval_line.mapped('level')
            if len(levels) != len(set(levels)):
                raise ValidationError('Levels must be different!') 