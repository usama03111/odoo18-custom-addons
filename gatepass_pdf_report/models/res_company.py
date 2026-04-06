from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    gatepass_enabled = fields.Boolean(
        string='Enable Gate Pass',
        help='If enabled, Gate Pass button/report will be available for invoices of this company.'
    )
