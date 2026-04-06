# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_allow_multi_user = fields.Boolean(
        related='company_id.sh_allow_multi_user', string='Allow Multi User To Start Task', readonly=False)
