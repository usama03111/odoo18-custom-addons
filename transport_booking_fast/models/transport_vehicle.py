from odoo import models, fields

class TransportVehicle(models.Model):
    _name = 'transport.vehicle'
    _description = 'Transport Vehicle'

    name = fields.Char(string='Vehicle Name', required=True)
    capacity = fields.Integer(string='Capacity', required=True)
