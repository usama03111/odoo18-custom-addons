# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models


class TaskApprovalConfigLine(models.Model):
    _name = 'sh.task.approval.config.line'
    _description = 'Task Approval Configuration Line'
    _order = 'level'

    task_approval_config_id = fields.Many2one(
        'sh.task.approval.config', string="Task Approval Configuration")
    level = fields.Integer(string="Level", required=True)
    approve_by = fields.Selection([
        ('user', 'Users'),
        ('group', 'Groups')
    ], string="Approve By", default='user', required=True)
    user_ids = fields.Many2many('res.users', string="Users")
    group_ids = fields.Many2many('res.groups', string="Groups") 