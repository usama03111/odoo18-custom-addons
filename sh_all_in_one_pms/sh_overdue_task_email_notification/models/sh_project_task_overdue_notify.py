# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models

class ProjectTaskOverdueNotify(models.Model):
    _name = "sh.project.task.overdue.notify"
    _description = 'Project Task Overdue Notify'

    name = fields.Char("Task")
    project_id = fields.Char("Project")
    user_ids = fields.Many2many("res.users",string="Assigned To")
    date_deadline = fields.Date("Date Deadline")

    email_id = fields.Many2one("sh.project.task.overdue.email", string="Email Id")
