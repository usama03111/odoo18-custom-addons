# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_task_custom_field = fields.Boolean(
        "Enable Task Custom Fields ",
        implied_group='sh_all_in_one_pms.group_task_custom_field')
