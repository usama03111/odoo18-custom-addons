# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RmaRequest(models.Model):
    _name = "rma.request"
    _description = "RMA Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    # --- Identity ---
    name = fields.Char(string="RMA", default="New", copy=False, index=True, tracking=True, readonly=True)
    # --- Company / Currency ---
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company,
                                 index=True, )
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", store=True, readonly=True, )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True, index=True)
    user_id = fields.Many2one("res.users", string="Salesperson", default=lambda self: self.env.user, index=True)
    sale_id = fields.Many2one("sale.order", string="Related Sales Order", index=True)
    picking_id = fields.Many2one("stock.picking", string="Related Delivery", index=True)
    picking_type = fields.Many2one('stock.picking.type', string="Operation Type")
    # location_dest_id = fields.Many2one('stock.location', string="Destination Location")
    # --- Core RMA info ---
    rma_type = fields.Selection(
        [("return", "Return"), ("replacement", "Replacement"),
         ("refund", "Refund"), ("repair", "Repair"), ],
        string="Request Type", required=True, default="return", tracking=True, index=True, )
    # Keep reason simple for step 1 (Char). We can switch to a Many2one (rma.reason) later.
    reason = fields.Selection([
        ('defect', 'Product Defect'),
        ('damage', 'Shipping Damage'),
        ('wrong_item', 'Wrong Item Sent'),
        ('not_as_described', 'Not as Described'),
        ('customer_error', 'Customer Error'),
        ('change_of_mind', 'Change of Mind'),
        ('warranty', 'Warranty Claim'),
        ('expire', 'Expired'),
        ('other', 'Other')
    ], string='Reason', required=True, default='other')

    reason_note = fields.Text(string="Reason Details")
    priority = fields.Selection([("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")], default="1",
                                tracking=True, )
    expected_resolution_date = fields.Date(string="Expected Resolution Date")
    # Amount field kept simple for now (no lines yet).
    amount_total = fields.Monetary(string="Estimated Amount", default=0.0)
    # --- State machine ---
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"),
         ("processing", "Processing"), ("done", "Done"), ("cancel", "Cancelled"), ],
        default="draft", tracking=True, index=True, )
    # --- Internal notes ---
    note_internal = fields.Text(string="Internal Notes")

    # --- Create sequence ---
    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            seq = self.env["ir.sequence"].next_by_code("rma.sequence")
            if seq:
                vals["name"] = seq
        return super().create(vals)

    @api.onchange("picking_id")
    def _onchange_picking_id(self):
        """Auto fill customer, sale order, and products when delivery is selected."""
        if self.picking_id:
            self.partner_id = self.picking_id.partner_id.id

            # Attempt to get the related sale order via origin
            sale_order = self.env['sale.order'].search([('name', '=', self.picking_id.origin)], limit=1)
            self.sale_id = sale_order.id if sale_order else False

            # Reset existing lines
            self.line_ids = [(5, 0, 0)]

            lines = []
            for move in self.picking_id.move_ids_without_package:
                lines.append((
                    0, 0, {
                    "product_id": move.product_id.id,
                    "qty": move.product_uom_qty,
                     "uom_id": move.product_id.uom_id.id,
                    # "uom_id": move.product_uom.id,
                }
                ))
            self.line_ids = lines

    # --- State actions ---
    def action_submit(self):
        for rec in self:
            rec._check_ready_to_submit()
            rec.state = "submitted"

    def action_approve(self):
        for rec in self:
            if rec.state not in ("submitted"):
                raise ValidationError(_("Only submitted/rejected RMAs can be approved."))
            rec.state = "approved"

    def action_reset(self):
        for rec in self:
            if rec.state not in ("cancel", "done"):
                raise ValidationError(_("Only submitted/approved RMAs can be rejected."))
            rec.state = "draft"

    def action_process(self):
        for rec in self:
            if rec.state != "approved":
                raise ValidationError(_("Only approved RMAs can be set to processing."))
            rec.state = "processing"

    def action_done(self):
        for rec in self:
            if rec.state not in ("processing", "approved"):
                raise ValidationError(_("Only processing/approved RMAs can be set to done."))

            if not rec.picking_id:
                raise ValidationError(_("You must select a related delivery (picking) before completing the RMA."))

            Picking = self.env["stock.picking"]
            Move = self.env["stock.move"]

            # ensure picking type for returns exists
            return_picking_type = rec.picking_id.picking_type_id.return_picking_type_id
            if not return_picking_type:
                raise ValidationError(_("No return picking type configured for this delivery type."))

            # Create the return picking (Inbound from customer)
            return_picking_vals = {
                "partner_id": rec.picking_id.partner_id.id,
                "picking_type_id": return_picking_type.id,
                "location_id": rec.picking_id.location_dest_id.id,  # from customer
                "location_dest_id": return_picking_type.default_location_dest_id.id
                                    or rec.picking_id.picking_type_id.warehouse_id.lot_stock_id.id,
                "origin": rec.picking_id.name, # optional if you add rma_id field in stock.picking
                "rma_id": rec.id,
            }
            return_picking = Picking.create(return_picking_vals)

            # Create stock moves for each RMA line
            for line in rec.line_ids:
                if not line.product_id:
                    continue
                Move.create({
                    "name": line.product_id.display_name,
                    "product_id": line.product_id.id,
                    "product_uom_qty": line.qty,
                    "product_uom": line.uom_id.id,
                    "picking_id": return_picking.id,
                    "location_id": rec.picking_id.location_dest_id.id,  # from customer
                    "location_dest_id": return_picking.location_dest_id.id,
                     "state" : 'done',
                     "quantity" : line.qty,
                })

            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            # Cancellation allowed from any non-final state
            if rec.state in ("done",):
                raise ValidationError(_("Completed RMAs cannot be cancelled."))
            rec.state = "cancel"

    # --- Helpers ---
    def _check_ready_to_submit(self):
        """Basic validations before submitting; expand later when we add lines."""
        for rec in self:
            if not rec.partner_id:
                raise ValidationError(_("Customer is required to submit the RMA."))
            if not rec.rma_type:
                raise ValidationError(_("Request Type is required to submit the RMA."))

    line_ids = fields.One2many("rma.request.line", "request_id", string="RMA Lines", copy=True)

    @api.depends("line_ids.subtotal")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped("subtotal"))

    amount_total = fields.Monetary(string="Total Amount", store=True, readonly=True, compute="_compute_amount_total",
                                   currency_field="currency_id")
    rma_count = fields.Integer(  string="Return Count", compute="_compute_rma_count", store=True)
    return_ids = fields.One2many('stock.picking', 'rma_id', string="Return Pickings")


    def action_open_warehouse_in(self):
        self.ensure_one()
        if len(self.return_ids) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "views": [[False, "form"]],
                "res_id": self.return_ids.id
            }
        return {
            'name': _('RMA Warehouse IN'),
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "views": [[False, "list"], [False, "form"]],
            "domain": [('id', 'in', self.return_ids.ids)],
        }

    @api.depends('return_ids')
    def _compute_rma_count(self):
        for rec in self:
            rec.rma_count = len(rec.return_ids)



# -------------------------RMA Line --------------------------------------------------------------------


class RmaRequestLine(models.Model):
    _name = "rma.request.line"
    _description = "RMA Request Line"
    _order = "id asc"

    request_id = fields.Many2one("rma.request", string="RMA Request", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product", string="Product", required=True, domain=[("sale_ok", "=", True)])
    qty = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    price_unit = fields.Float(string="Unit Price")
    subtotal = fields.Monetary(string="Subtotal", compute="_compute_subtotal", store=True)
    currency_id = fields.Many2one(related="request_id.currency_id", string="Currency", store=True)

    @api.depends("qty", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.price_unit

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_id.id
                line.price_unit = line.product_id.lst_price

    @api.constrains("qty")
    def _check_qty_positive(self):
        for line in self:
            if line.qty <= 0:
                raise ValidationError("Quantity must be greater than zero.")

    @api.onchange('qty', 'product_id')
    def _onchange_qty_check(self):
        for line in self:
            if not line.product_id or not line.request_id.picking_id:
                continue
            delivered_qty = sum(
                line.request_id.picking_id.move_ids_without_package.filtered(
                    lambda m: m.product_id == line.product_id
                ).mapped('product_uom_qty')
            )
            previous_rma_qty = sum(
                self.env['rma.request.line'].search([
                    ('request_id.picking_id', '=', line.request_id.picking_id.id),
                    ('product_id', '=', line.product_id.id),
                    ('request_id.state', 'in', ['processing', 'done']),
                    ('id', '!=', line.id),
                ]).mapped('qty')
            )
            max_return = delivered_qty - previous_rma_qty
            if line.qty > max_return:
                line.qty = max_return
                return {
                    'warning': {
                        'title': "Quantity Adjusted",
                        'message': "You cannot return more than delivered. Maximum allowed: %s" % max_return
                    }
                }




# ----------------------------Stock Inherit-------------------------------------------------------------
from odoo import models, fields, _

class InheritStock(models.Model):
    _inherit = 'stock.picking'

    # Optional: link the first RMA (can be used in smart button)
    rma_id = fields.Many2one('rma.request', string="Related RMA")

    # Count of RMAs linked to this delivery
    rma_count = fields.Integer(
        string="RMA Count",
        compute='_compute_rma_count',
    )

    def _compute_rma_count(self):
        for picking in self:
            picking.rma_count = self.env['rma.request'].search_count([('picking_id', '=', picking.id)])

    def action_open_warehouse_in(self):
        """Open linked RMA requests: tree view if multiple, form view if one"""
        self.ensure_one()
        rma_records = self.env['rma.request'].search([('picking_id', '=', self.id)])

        if not rma_records:
            # No RMAs linked, do nothing or return a warning
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No RMA found'),
                    'message': _('There are no RMA requests linked to this delivery.'),
                    'type': 'warning',
                    'sticky': False,
                },
            }

        if len(rma_records) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "rma.request",
                "views": [[False, "form"]],
                "res_id": rma_records.id,
            }

        return {
            'name': _('RMA Warehouse IN'),
            "type": "ir.actions.act_window",
            "res_model": "rma.request",
            "views": [[False, "list"], [False, "form"]],
            "domain": [('id', 'in', rma_records.ids)],
        }

