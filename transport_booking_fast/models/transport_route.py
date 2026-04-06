from odoo import models, fields

class TransportRoute(models.Model):
    _name = 'transport.route'
    _description = 'Transport Route'

    name = fields.Char(string='Name', required=True)
    start_location = fields.Char(string='From', required=True)
    end_location = fields.Char(string='To', required=True)
