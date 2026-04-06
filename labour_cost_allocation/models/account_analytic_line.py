from odoo import models, fields

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    payslip_id = fields.Many2one('hr.payslip', string='Payslip', ondelete='cascade', readonly=True)
