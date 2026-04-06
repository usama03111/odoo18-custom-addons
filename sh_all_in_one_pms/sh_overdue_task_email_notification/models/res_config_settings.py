# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    notification = fields.Boolean("Overdue Notification")
    overdue_days = fields.Integer("Overdue Days")

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    notification = fields.Boolean(
        related="company_id.notification",
        string="Overdue Notification",
        readonly=False
    )
    overdue_days = fields.Integer(
        related="company_id.overdue_days",
        string="Overdue Days",
        readonly=False
    )
