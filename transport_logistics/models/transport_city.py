from odoo import models, fields

class TransportCity(models.Model):
    _name = 'transport.city'
    _description = 'Transport City'
    _order = 'name'

    name = fields.Char(string='City Name', required=True)
    code = fields.Char(string='City Code')
