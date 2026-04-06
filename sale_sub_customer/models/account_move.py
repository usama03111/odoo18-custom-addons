from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    has_sub_customer = fields.Boolean(string="Has Sub Customer")

    sub_customer_id = fields.Many2one(
        'res.partner',
        string="Sub Customer"
    )
