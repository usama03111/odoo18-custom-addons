from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Checkbox to control whether Sub Customer should be used
    has_sub_customer = fields.Boolean(string="Has Sub Customer")

    # Sub Customer field (child contact of selected customer)
    sub_customer_id = fields.Many2one(
        'res.partner',
        string="Sub Customer"
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_sub_customer_domain(self):
        """
                When Customer changes:
                - Clear previously selected Sub Customer
                - Dynamically restrict Sub Customer to contacts
                  of the commercial (parent) customer
                """
        self.sub_customer_id = False
        if self.partner_id:
            return {
                'domain': {
                    'sub_customer_id': [
                        ('parent_id', '=', self.partner_id.commercial_partner_id.id)
                    ]
                }
            }

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({
            'has_sub_customer': self.has_sub_customer,
            'sub_customer_id': self.sub_customer_id.id,
        })
        return vals
