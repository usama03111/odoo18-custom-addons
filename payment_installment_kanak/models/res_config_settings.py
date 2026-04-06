# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enable_installments = fields.Boolean(
        "Installment On Sales",
        related="company_id.enable_installments",
        readonly=False,
    )

    installment_invoice_settings = fields.Selection(
        related="company_id.installment_invoice_settings",
        string="Installment Invoice Settings",
        readonly=False,
    )
    days_before_invoice = fields.Integer(
        "Days before", related="company_id.days_before_invoice", readonly=False
    )





class ResCompany(models.Model):
    _inherit = "res.company"

    installment_invoice_settings = fields.Selection(
        [
            ("single_invoice", "Single Invoice"),
            ("multiple_invoice", "Multiple Invoice"),
        ],
        string="Installments Invoice Settings",
        default="single_invoice",
    )
    days_before_invoice = fields.Integer()
    enable_installments = fields.Boolean()

