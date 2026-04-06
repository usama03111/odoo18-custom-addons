from odoo import models, fields

class AnalyticAccountWithFoodicsBranchName(models.Model):
    _inherit = 'account.analytic.account'

    foodics_branch_id = fields.Char(string='Foodics Branch Identifier', readonly=True)
