from odoo import models, fields, api, _

class TransportBuilty(models.Model):
    _name = 'transport.builty'
    _description = 'Builty (Consignment Note)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'

    name = fields.Char(string='Builty #', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    
    # Route
    source_city_id = fields.Many2one('transport.city', string='From City', required=True, tracking=True)
    dest_city_id = fields.Many2one('transport.city', string='To City', required=True, tracking=True)

    branch_id = fields.Many2one('transport.branch', string='Branch', ) # To be linked to user later

    # Sender & Receiver
    sender_id = fields.Many2one('res.partner', string='Sender', required=True, tracking=True)
    sender_phone = fields.Char(related='sender_id.phone', readonly=False, store=True)
    sender_cnic = fields.Char(string='Sender CNIC') # Custom field not on res.partner by default? Assuming we keep it here or add to partner.

    receiver_id = fields.Many2one('res.partner', string='Receiver', required=True, tracking=True)
    receiver_phone = fields.Char(related='receiver_id.phone', readonly=False, store=True)
    receiver_address = fields.Text(string='Delivery Address')

    # Cargo Details
    item_count = fields.Integer(string='Total Items/Nag', required=True, default=1)
    weight = fields.Float(string='Weight (kg)')
    is_estimated_weight = fields.Boolean(string='Estimated Weight?')
    volume_cbm = fields.Float(string='Volume (CBM)')
    description = fields.Text(string='Description / Tafseel-e-Maal')

    # Service Type
    service_type = fields.Selection([
        ('counter', 'Counter Collection'),
        ('door', 'Door Delivery'),
    ], string='Service', default='counter', required=True)
    pickup_location = fields.Char(string='Pickup Location (if Any)')

    # Charges
    charges_fare = fields.Monetary(string='Fare', currency_field='currency_id', required=True)
    charges_labor = fields.Monetary(string='Labor Charges', currency_field='currency_id')
    charges_service = fields.Monetary(string='Service Charges', currency_field='currency_id')
    amount_total = fields.Monetary(string='Total Amount', compute='_compute_amount_total', store=True, currency_field='currency_id')
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # Payment
    payment_type = fields.Selection([
        ('cod', 'Cash on Delivery (COD)'),
        ('advance', 'Advance'),
        ('credit', 'Credit / Post-pay'),
    ], string='Payment Type', default='cod', required=True)
    
    amount_paid = fields.Monetary(string='Paid Amount', currency_field='currency_id')
    amount_remaining = fields.Monetary(string='Remaining', compute='_compute_amount_remaining', store=True, currency_field='currency_id')

    batch_id = fields.Many2one('transport.batch', string='Manifest / Loading Sheet', readonly=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('booked', 'Booked'),
        ('transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    remarks = fields.Text(string='Remarks')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('transport.builty') or _('New')
        return super().create(vals_list)

    @api.depends('charges_fare', 'charges_labor', 'charges_service')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.charges_fare + rec.charges_labor + rec.charges_service

    @api.depends('amount_total', 'amount_paid')
    def _compute_amount_remaining(self):
        for rec in self:
            rec.amount_remaining = rec.amount_total - rec.amount_paid

    def action_confirm(self):
        self.write({'state': 'booked'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.onchange('dest_city_id')
    def _onchange_dest_city_id(self):
        self.branch_id = False
        if self.dest_city_id:
            return {
                'domain': {
                    'branch_id': [('city_id', '=', self.dest_city_id.id)]
                }
            }