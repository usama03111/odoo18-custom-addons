# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_milestone_manager = fields.Boolean("Milestone Manager ?")
