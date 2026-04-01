from odoo import api, fields, models


class PayrollCategoryApprover(models.Model):

    _name = 'payroll.category.approver'
    _description = 'Payroll Category Approver'
    _rec_name = 'user_id'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', default=10)
    approver_id = fields.Many2one('payroll.approver', string='Approval Type', ondelete='cascade', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True, default=lambda self: self.env.company)

    user_id = fields.Many2one(
        'res.users', string='User', ondelete='cascade', required=True,
        check_company=True, domain="[('id', 'not in', existing_user_ids)]")


    required = fields.Boolean(default=False)

    existing_user_ids = fields.Many2many('res.users', compute='_compute_existing_user_ids')

    @api.depends('approver_id')
    def _compute_existing_user_ids(self):
        for record in self:
            record.existing_user_ids = record.approver_id.approver_ids.user_id
