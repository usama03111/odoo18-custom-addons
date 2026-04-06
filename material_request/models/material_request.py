from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class MaterialRequest(models.Model):
    _name = 'material.request'
    _description = 'Material Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Request Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True)
    user_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, readonly=True)
    date = fields.Date(string='Request Date', default=fields.Date.context_today, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    line_ids = fields.One2many('material.request.line', 'request_id', string='Material Lines')
    purchase_order_ids = fields.One2many('purchase.order', 'material_request_id', string='RFQs')
    purchase_count = fields.Integer(string='RFQ Count', compute='_compute_purchase_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('material.request') or _('New')
        return super(MaterialRequest, self).create(vals_list)

    @api.depends('purchase_order_ids')
    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec.purchase_order_ids)

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('You cannot submit a request without any products.'))
            for line in rec.line_ids:
                if line.quantity <= 0:
                    raise UserError(_('Quantity must be greater than 0 for product %s.') % line.product_id.name)
            if not rec.project_id.user_id:
                raise UserError(_('The project must have a Project Manager assigned before you can submit.'))
            rec.state = 'submitted'
            
            # Activity to the  Project Manager
            if rec.project_id.user_id:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=rec.project_id.user_id.id,
                    summary=_('Review Material Request'),
                    note=_('A new material request has been submitted for your project.')
                )

    def action_approve(self):
        self.ensure_one()
        # Only Project Managers can approve requests

        if self.project_id.user_id != self.env.user:
            raise UserError(_('Only the assigned Project Manager (%s) can approve this request.') % self.project_id.user_id.name)
        if self.state != 'submitted':
             return
        if self.purchase_order_ids:
             raise UserError(_('An RFQ has already been generated for this request.'))

        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        
        po_vals = {
            'partner_id': self.env.user.partner_id.id, 
             'origin': self.name,
             'material_request_id': self.id,
        }
        
        # Create PO and Lines
        
        po = PurchaseOrder.create(po_vals)
        
        for line in self.line_ids:
            PurchaseOrderLine.create({
                'order_id': po.id,
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom': line.uom_id.id,
                'name': line.description or line.product_id.name,
                'date_planned': fields.Date.today(),
                'price_unit': 0.0,
            })

        self.state = 'approved'

    #  Prevent cancelling if RFQ is already processed in the XMl to hide Button
    #  (logic can be expanded later if we needed )
    def action_cancel(self):
        self.ensure_one()
        if self.purchase_order_ids:
             pass
        self.state = 'cancelled'

    # we cannot delete an approved material request
    def unlink(self):
        for rec in self:
            if rec.state == 'approved':
                raise UserError(_('You cannot delete an approved material request.'))
        return super(MaterialRequest, self).unlink()

    # action to view the RFQs
    def action_view_rfq(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'RFQs',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_ids.id,
            'context': {'create': False},
        }

class MaterialRequestLine(models.Model):
    _name = 'material.request.line'
    _description = 'Material Request Line'

    request_id = fields.Many2one('material.request', string='Request', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    description = fields.Char(string='Description')

    # onchange function to set the uom_id and description based on the product_id
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.description = self.product_id.name


    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Quantity must be positive.'))

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    material_request_id = fields.Many2one('material.request', string='Material Request', readonly=True)
