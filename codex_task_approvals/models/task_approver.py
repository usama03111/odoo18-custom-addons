from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError


class TaskApprover(models.Model):
    _name = "task.approver"
    _description = "Task Approver"
    _rec_name = 'name'

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    user_ids = fields.Many2many('res.users', compute='_compute_user_ids', string="Approver Users")
    request_to_validate_count = fields.Integer("Tasks to Approve", compute="_compute_request_to_validate_count")
    
    to_approve_previous_approver = fields.Boolean(
        'Return to Previous Approver', 
        help="When enabled, if an approver rejects the task, it will be returned to the previous approver for review."
    )
    on_rejection_approval_restart = fields.Boolean(
        'Restart Approval Process on Rejection',
        help="When enabled, if any approver rejects the task, the approval process will restart from the first approver."
    )

    @api.constrains('to_approve_previous_approver', 'on_rejection_approval_restart')
    def _check_rejection_handling(self):
        for record in self:
            if record.to_approve_previous_approver and record.on_rejection_approval_restart:
                raise ValidationError(_("You can only select one rejection handling method: either 'Return to Previous Approver' or 'Restart Approval Process on Rejection'"))

    automated_sequence = fields.Boolean('Automated Sequence?')
    sequence_code = fields.Char(string="Code")
    sequence_id = fields.Many2one('ir.sequence', string='Reference Sequence', copy=False, check_company=True)

    approver_ids = fields.One2many('task.category.approver', 'approver_id', string="Approvers")
    approver_sequence = fields.Boolean('Sequence Approval?')
    approval_minimum = fields.Integer(string="Minimum Approval", default=1, required=True)

    invalid_minimum = fields.Boolean(compute='_compute_invalid_minimum')
    invalid_minimum_warning = fields.Char(compute='_compute_invalid_minimum')

    # @api.depends('approval_minimum', 'approver_ids')
    # def _compute_invalid_minimum(self):
    #     for record in self:
    #         record.invalid_minimum = record.approval_minimum > len(record.approver_ids)
    #         record.invalid_minimum_warning = ((
    #             'Your minimum approval exceeds the total number of approvers.'
    #             if record.invalid_minimum else ''
    #         ) )

    @api.depends('approval_minimum', 'approver_ids')
    def _compute_invalid_minimum(self):
        for record in self:
            if record.approval_minimum > len(record.approver_ids):
                record.invalid_minimum = True
            else:
                record.invalid_minimum = False
            record.invalid_minimum_warning = record.invalid_minimum and _(
                'Your minimum approval exceeds the total of default approvers.')

    @api.depends('approver_ids')
    def _compute_user_ids(self):
        for record in self:
            record.user_ids = record.approver_ids.mapped('user_id')

    def _compute_request_to_validate_count(self):
        domain = [('state', '=', 'pending'), ('approver_ids.user_id', '=', self.env.user.id)]
        result = self.env['project.task']._read_group(domain, ['approver_id'], ['__count'])
        counts = {r['approver_id'][0]: r['__count'] for r in result if r['approver_id']}
        for record in self:
            record.request_to_validate_count = counts.get(record.id, 0)

