from odoo import models, fields

class TransportBranch(models.Model):
    _name = 'transport.branch'
    _description = 'Transport Branch'

    name = fields.Char(string='Branch Name', required=True)
    code = fields.Char(string='Code')
    city_id = fields.Many2one('transport.city', string='City')

    phone = fields.Char(string='Phone')
    address = fields.Text(string='Address')
