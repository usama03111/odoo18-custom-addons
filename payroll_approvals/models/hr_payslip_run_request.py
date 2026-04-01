from odoo import models, api, fields, Command, _
from odoo.api import ondelete
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    approver_id = fields.Many2one('payroll.approver', tracking=True)
    approver_sequence = fields.Boolean(related="approver_id.approver_sequence")
    approval_minimum = fields.Integer(related="approver_id.approval_minimum")
    reason = fields.Char('Reason', tracking=True)
    rejection_reason = fields.Text('Rejection Reason', tracking=True, )

    state = fields.Selection(selection_add=[
        ('cancel', 'Cancel'),
        ('under_approved', 'Under Approved'),
        ('01_approved', 'Approved'),
    ], string='Status', index=True, copy=False, tracking=True,
        ondelete={'under_approved': 'set default', '01_approved': 'set default',}
    )

    user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel')
    ], compute="_compute_user_status")

    approver_ids = fields.One2many('payroll.payslip.approver', 'task_id', string="Approvers",
                                   compute='_compute_approver_ids', store=True, readonly=False)


    def send_for_approvals(self):
        self.ensure_one()
        if len(self.approver_ids) < self.approval_minimum:
            raise UserError(_("You have to add at least %s approvers to confirm your task.", self.approval_minimum))

        approvers = self.approver_ids
        if self.approver_sequence:
            # Reset all approvers if needed
            if self.state == 'under_approved' and any(a.status != 'new' for a in approvers):
                approvers.write({'status': 'new'})
            approvers = approvers.filtered(lambda a: a.status in ['new', 'pending', 'waiting'])
            # Set first to pending, rest to waiting
            if approvers:
                approvers[0].sudo().write({'status': 'pending'})
                if len(approvers) > 1:
                    approvers[1:].sudo().write({'status': 'waiting'})
        else:
            approvers = approvers.filtered(lambda a: a.status == 'new')
            approvers.sudo().write({'status': 'pending'})
        self.sudo().write({'state': 'under_approved'})
        # Now create activity only for the pending approver
        self.approver_ids._create_activity()

    def _update_task_state(self, statuses, required_approved, minimal_approved):
        """Helper method to determine task state based on approvals"""
        if 'cancel' in statuses:
            return 'cancel'
        elif all(s == 'approved' for s in statuses) and len(statuses) > 0:
            return '01_approved'
        elif any(s in ['pending', 'waiting', 'approved'] for s in statuses):
            return 'under_approved'
        return 'under_approved'

    def action_approve(self, approver=None):
        self._ensure_can_approve()
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        approver.write({'status': 'approved'})
        self.write({'rejection_reason': False})
        self._update_next_approvers('pending', approver, only_next_approver=True)
        # Mark activity as done for this approver
        activity_type = self.env.ref('payroll_approvals.mail_activity_data_payslip_payroll_run')
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'hr.payslip.run'),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
            ('user_id', '=', approver.user_id.id),
            ('state', '=', 'planned'),
        ])
        if activity:
            activity.action_feedback()
        for task in self:
            statuses = task.mapped('approver_ids.status')
            # If all approvers approved, set to 01_approved
            if all(s == 'approved' for s in statuses) and len(statuses) > 0:
                state = '01_approved'
            else:
                state = 'under_approved'
            task.write({'state': state})
            if state == 'under_approved':
                next_approvers = task.approver_ids.filtered(lambda a: a.status == 'pending')
                for approver in next_approvers:
                    approver._create_activity()

    def action_cancel(self, approver=None, rejection_reason=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        # If on_rejection_approval_restart is enabled
        if self.approver_id.on_rejection_approval_restart:
            self.approver_ids.write({'status': 'new'})
            first_approver = self.approver_ids.sorted(lambda a: a.sequence)[0]
            first_approver.write({'status': 'pending'})
            first_approver._create_activity()
            self.write({
                'state': 'under_approved',
                'rejection_reason': rejection_reason or False
            })
            # Mark activity as done for this approver
            activity_type = self.env.ref('payroll_approvals.mail_activity_data_payslip_payroll_run')
            activity = self.env['mail.activity'].search([
                ('res_model', '=', 'hr.payslip.run'),
                ('res_id', '=', self.id),
                ('activity_type_id', '=', activity_type.id),
                ('user_id', '=', approver.user_id.id),
                ('state', '=', 'planned'),
            ])
            if activity:
                activity.action_feedback()
            self._get_user_approval_activities(user=self.env.user).action_feedback()
            return
        elif self.approver_id.to_approve_previous_approver and self.approver_sequence:
            current_approver = approver
            previous_approvers = self.approver_ids.filtered(
                lambda a: a.sequence < current_approver.sequence and a.status == 'approved'
            )
            if previous_approvers:
                previous_approver = previous_approvers.sorted(lambda a: a.sequence, reverse=True)[0]
                self.approver_ids.filtered(
                    lambda a: a.sequence >= current_approver.sequence
                ).write({'status': 'waiting'})
                previous_approver.write({'status': 'pending'})
                previous_approver._create_activity()
                self.write({
                    'state': 'under_approved',
                    'rejection_reason': rejection_reason or False
                })
                # Mark activity as done for this approver
                activity_type = self.env.ref('payroll_approvals.mail_activity_data_payslip_payroll_run')
                activity = self.env['mail.activity'].search([
                    ('res_model', '=', 'hr.payslip.run'),
                    ('res_id', '=', self.id),
                    ('activity_type_id', '=', activity_type.id),
                    ('user_id', '=', approver.user_id.id),
                    ('state', '=', 'planned'),
                ])
                if activity:
                    activity.action_feedback()
                self._get_user_approval_activities(user=self.env.user).action_feedback()
                return
        # Default cancellation behavior if no special handling is enabled
        approver.write({'status': 'cancel'})
        # If first approver is rejecting, set to 1_canceled, else under_approved
        first_approver = self.approver_ids.sorted(lambda a: a.sequence)[0]
        if approver.id == first_approver.id:
            state = 'cancel'
        else:
            state = 'under_approved'
        self.write({
            'state': state,
            'rejection_reason': rejection_reason or False
        })
        # Mark activity as done for this approver
        activity_type = self.env.ref('payroll_approvals.mail_activity_data_payslip_payroll_run')
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'hr.payslip.run'),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
            ('user_id', '=', approver.user_id.id),
            ('state', '=', 'planned'),
        ])
        if activity:
            activity.action_feedback()
        self._update_next_approvers('cancel', approver, only_next_approver=False, cancel_activities=True)
        self._get_user_approval_activities(user=self.env.user).action_feedback()

    def action_withdraw(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        self._update_next_approvers('waiting', approver, only_next_approver=False, cancel_activities=True)
        approver.write({'status': 'pending'})

    def _update_next_approvers(self, new_status, approver, only_next_approver, cancel_activities=False):
        approvers_updated = self.env['payroll.payslip.approver']
        for task in self.filtered('approver_sequence'):
            current = task.approver_ids & approver
            next_approvers = task.approver_ids.filtered(lambda a: a.status not in ['approved', 'cancel'] and (
                    a.sequence > current.sequence or (a.sequence == current.sequence and a.id > current.id)))
            if only_next_approver and next_approvers:
                next_approvers = next_approvers[0]
            approvers_updated |= next_approvers
        approvers_updated.sudo().write({'status': new_status})
        if new_status == 'pending':
            approvers_updated._create_activity()
        if cancel_activities:
            approvers_updated.task_id._cancel_activities()

    def _cancel_activities(self):
        activity_type = self.env.ref('payroll_approvals.mail_activity_data_payslip_payroll_run')
        self.activity_ids.filtered(lambda a: a.activity_type_id == activity_type).unlink()

    def _get_user_approval_activities(self, user):
        return self.env['mail.activity'].search([
            ('res_model', '=', 'hr.payslip.run'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('payroll_approvals.mail_activity_data_payslip_payroll_run').id),
            ('user_id', '=', user.id)
        ])

    @api.depends('approver_ids.status')
    def _compute_user_status(self):
        for task in self:
            task.user_status = task.approver_ids.filtered(lambda a: a.user_id == self.env.user).status

    def _ensure_can_approve(self):
        if any(task.approver_sequence and task.user_status == 'waiting' for task in self):
            raise ValidationError(_('You cannot approve before the previous approver.'))

    @api.model
    def _update_approver_vals(self, approver_id_vals, approver, new_required, new_sequence):
        if approver.required != new_required or approver.sequence != new_sequence:
            approver_id_vals.append(
                Command.update(approver.id, {'required': new_required, 'sequence': new_sequence}))

    @api.model
    def _create_or_update_approver(self, user_id, users_to_approver, approver_id_vals, required, sequence):
        if user_id not in users_to_approver.keys():
            approver_id_vals.append(Command.create({
                'user_id': user_id,
                'status': 'new',
                'required': required,
                'sequence': sequence,
            }))
        else:
            current_approver = users_to_approver.pop(user_id)
            self._update_approver_vals(approver_id_vals, current_approver, required, sequence)

    @api.depends('approver_id')
    def _compute_approver_ids(self):
        for task in self:
            if not task.approver_id:
                task.approver_ids = [(5, 0, 0)]  # Clear all approvers
                continue

            current_approvers = {a.user_id.id: a for a in task.approver_ids}
            required_approvers = {a.user_id.id: a for a in task.approver_id.approver_ids}
            commands = []

            # Add or update approvers
            for user_id, required_approver in required_approvers.items():
                if user_id in current_approvers:
                    current = current_approvers.pop(user_id)
                    if current.required != required_approver.required or current.sequence != required_approver.sequence:
                        commands.append(Command.update(current.id, {
                            'required': required_approver.required,
                            'sequence': required_approver.sequence,
                        }))
                else:
                    commands.append(Command.create({
                        'user_id': user_id,
                        'status': 'new',
                        'required': required_approver.required,
                        'sequence': required_approver.sequence,
                    }))

            # Remove any leftover old approvers
            for leftover in current_approvers.values():
                commands.append(Command.delete(leftover.id))
            task.approver_ids = commands

    @api.constrains('approver_ids')
    def _check_approver_ids(self):
        for request in self:
            if len(request.approver_ids) != len(request.approver_ids.user_id):
                raise UserError(_("You cannot assign the same approver multiple times on the same request."))

    def write(self, vals):
        res = super().write(vals)
        if 'approver_ids' in vals:
            resequence = self.filtered(lambda t: t.approver_sequence and t.state == 'under_approved')
            for task in resequence:
                if not task.approver_ids.filtered(lambda a: a.status == 'pending'):
                    pending = task.approver_ids.filtered(lambda a: a.status == 'waiting')
                    if pending:
                        pending[0].write({'status': 'pending'})
                        pending[0]._create_activity()
        return res


class PayrollPayslipApprover(models.Model):
    _name ='payroll.payslip.approver'
    _description = 'Payroll Payslip Line'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    user_id = fields.Many2one('res.users', string="User", required=True, check_company=True,
                              domain="[('id', 'not in', existing_request_user_ids)]")
    existing_request_user_ids = fields.Many2many('res.users', compute='_compute_existing_request_user_ids')
    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel')
    ], string="Status", default="new", readonly=True)

    task_id = fields.Many2one('hr.payslip.run', string="Task", ondelete='cascade', check_company=True)
    # company_id = fields.Many2one(related='task_id.company_id', store=True, readonly=True, index=True)
    required = fields.Boolean(default=False, readonly=True)
    category_approver = fields.Boolean(compute='_compute_category_approver')
    can_edit = fields.Boolean(compute='_compute_can_edit')
    can_edit_user_id = fields.Boolean(compute='_compute_can_edit')

    def action_approve(self):
        self.task_id.action_approve(self)

    def action_refuse(self):
        """Legacy method to maintain compatibility"""
        return self.action_cancel()

    def action_cancel(self):
        self.task_id.action_cancel(self)

    def _create_activity(self):
        activity_type = self.env.ref('payroll_approvals.mail_activity_data_payslip_payroll_run')
        for approver in self:
            # Only create activity for the current approver (status == 'pending')
            if approver.status == 'pending':
                existing = self.env['mail.activity'].search([
                    ('res_model', '=', 'hr.payslip.run'),
                    ('res_id', '=', approver.task_id.id),
                    ('activity_type_id', '=', activity_type.id),
                    ('user_id', '=', approver.user_id.id),
                    ('state', '=', 'planned'),
                ])
                if not existing:
                    approver.task_id.activity_schedule(
                        'payroll_approvals.mail_activity_data_payslip_payroll_run',
                        user_id=approver.user_id.id
                    )

    @api.depends('task_id.approver_ids.user_id')
    def _compute_existing_request_user_ids(self):
        for approver in self:
            approver.existing_request_user_ids = approver.task_id.approver_ids.mapped('user_id')._origin

    @api.depends('category_approver', 'user_id')
    def _compute_category_approver(self):
        for a in self:
            a.category_approver = a.user_id in a.task_id.approver_id.approver_ids.mapped('user_id')

    @api.depends_context('uid')
    def _compute_can_edit(self):
        is_user = self.env.user.has_group('odoo_task_approvals.task_group_approval_users')
        for approval in self:
            approval.can_edit = not approval.user_id or not approval.category_approver or is_user
            approval.can_edit_user_id = is_user
