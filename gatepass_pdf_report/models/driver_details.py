from odoo import models, fields

class AccountMoveDriverDetails(models.Model):
    _inherit = "account.move"

    vehicle_no = fields.Char(string="Vehicle Number")
    driver_name = fields.Char(string="Driver Name")
    driver_contact = fields.Char(string="Driver Contact")
    goods_shipped_to = fields.Char(string="Goods Shipped To")
