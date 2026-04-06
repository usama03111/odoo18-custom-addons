# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models


class TaskApprovalInfo(models.Model):
    _name = 'sh.task.approval.info'
    _description = 'Task Approval Information'
    _order = 'level'

    sh_task_id = fields.Many2one('project.task', string="Task")
    level = fields.Integer(string="Level")
    user_ids = fields.Many2many('res.users', string="Users")
    group_ids = fields.Many2many('res.groups', string="Groups")
    status = fields.Boolean(string="Approved", default=False)
    approval_date = fields.Datetime(string="Approval Date")
    approved_by = fields.Many2one('res.users', string="Approved By") 