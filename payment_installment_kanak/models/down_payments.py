# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).


from odoo import models, fields


class DownPayments(models.Model):
    _name = "down.payment"
    _description = "Down Payments"
    _rec_name = "description"

    sale_order_id = fields.Many2one("sale.order")

    description = fields.Text("Description", required=True)
    amount = fields.Float("Amount", required=True)
    due_date = fields.Date("Date", required=True)