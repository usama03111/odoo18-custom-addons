from odoo import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'

    material_request_ids = fields.One2many('material.request', 'project_id', string='Material Requests')
    material_cost = fields.Monetary(string='Material Cost', compute='_compute_material_cost', currency_field='currency_id')

    @api.depends('material_request_ids.purchase_order_ids.amount_total',
                 'material_request_ids.purchase_order_ids.state')
    def _compute_material_cost(self):
        for project in self:
            total_cost = 0.0
            # Get all RFQs linked to the project material requests
            rfqs = project.material_request_ids.mapped('purchase_order_ids')
            rfqs = rfqs.filtered(lambda p: p.state != 'cancel')
            total_cost = sum(rfqs.mapped('amount_total'))
            project.material_cost = total_cost
