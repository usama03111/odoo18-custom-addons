from odoo import api, fields, models


class TaskCategoryApprover(models.Model):

    _name = 'task.category.approver'
    _description = 'Task Category Approver'
    _rec_name = 'user_id'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', default=10)
    approver_id = fields.Many2one('task.approver', string='Approval Type', ondelete='cascade', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True, default=lambda self: self.env.company)

    user_id = fields.Many2one(
        'res.users', string='User', ondelete='cascade', required=True,
        check_company=True, domain="[('id', 'not in', existing_user_ids)]")

    # user_id = fields.Many2one(
    #     'res.users', string='User', ondelete='cascade', required=True,
    #     check_company=True,)
    required = fields.Boolean(default=False)

    existing_user_ids = fields.Many2many('res.users', compute='_compute_existing_user_ids')

    @api.depends('approver_id')
    def _compute_existing_user_ids(self):
        for record in self:
            record.existing_user_ids = record.approver_id.approver_ids.user_id
