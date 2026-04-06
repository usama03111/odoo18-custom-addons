# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields

class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    group_enable_project_category = fields.Boolean(
        "Enable Project Category", implied_group='sh_all_in_one_pms.group_enable_project_category')
