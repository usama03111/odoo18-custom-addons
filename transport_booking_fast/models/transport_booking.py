from odoo import models, fields, api

class TransportBooking(models.Model):
    _name = 'transport.booking'
    _description = 'Transport Booking'

    route_id = fields.Many2one('transport.route', string='Route', required=True)
    vehicle_id = fields.Many2one('transport.vehicle', string='Vehicle', required=True)
    booking_date = fields.Datetime(string='Booking Date', default=fields.Datetime.now, required=True)
    customer_name = fields.Char(string='Customer Name', required=True)
    seats = fields.Integer(string='Seats', required=True)
    amount = fields.Float(string='Amount', required=True)

    @api.model
    def create_booking(self, data):
        """Creates a booking record from the provided dictionary `data`."""
        record = self.create({
            'route_id': int(data.get('route_id')),
            'vehicle_id': int(data.get('vehicle_id')),
            'customer_name': data.get('customer_name'),
            'seats': int(data.get('seats')),
            'amount': float(data.get('amount')),
        })
        return {'success': True, 'id': record.id}
