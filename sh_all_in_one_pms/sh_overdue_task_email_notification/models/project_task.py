# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
"""import the odoo and date time."""

from odoo import fields, models

class ProjectTask(models.Model):
    _inherit = 'project.task'

    completed = fields.Boolean("Task Completed", readonly=True)

    def action_task_completed(self):
        """method is used for the true the completed boolean."""
        self.completed = True
