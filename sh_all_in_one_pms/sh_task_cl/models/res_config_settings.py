# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_enable_task_checklist = fields.Boolean(
        "Enable Task Checklist ",
        implied_group='sh_all_in_one_pms.group_enable_task_checklist')
