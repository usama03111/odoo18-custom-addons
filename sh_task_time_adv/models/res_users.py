# Copyright (C) Softhealer Technologies.

from odoo import models, fields
from datetime import datetime

class User(models.Model):
    _inherit = 'res.users'

    task_id = fields.Many2one('project.task')
    start_time = fields.Datetime("Start Time", copy=False)
    end_time = fields.Datetime("End Time", copy=False)
