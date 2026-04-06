from odoo import models, fields, api, _

class TransportBatch(models.Model):
    _name = 'transport.batch'
    _description = 'Vehicle Loading Batch / Manifest'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'

    name = fields.Char(string='Manifest #', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    
    # Vehicle & Driver
    vehicle_no = fields.Char(string='Vehicle No.', required=True, tracking=True)
    driver_name = fields.Char(string='Driver Name', tracking=True) 
    driver_phone = fields.Char(string='Driver Phone')
    
    # Linked Builties
    builty_ids = fields.One2many('transport.builty', 'batch_id', string='Builties')
    
    # Totals
    total_weight = fields.Float(string='Total Weight', compute='_compute_totals', store=True)
    total_fare = fields.Monetary(string='Total Fare', compute='_compute_totals', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('loaded', 'Loaded'),
        ('shipped', 'Shipped'),
        ('arrived', 'Arrived'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('transport.batch') or _('New')
        return super().create(vals_list)

    @api.depends('builty_ids', 'builty_ids.weight', 'builty_ids.charges_fare')
    def _compute_totals(self):
        for rec in self:
            rec.total_weight = sum(rec.builty_ids.mapped('weight'))
            rec.total_fare = sum(rec.builty_ids.mapped('charges_fare'))

    def action_load(self):
        self.write({'state': 'loaded'})
        for builty in self.builty_ids:
            builty.state = 'transit'

    def action_ship(self):
        self.write({'state': 'shipped'})

    def action_arrive(self):
        self.write({'state': 'arrived'})
        for builty in self.builty_ids:
            builty.state = 'delivered' # Simplified workflow for now
