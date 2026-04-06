from odoo import models, api, fields, Command, _
from odoo.api import ondelete
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    approver_id = fields.Many2one('task.approver', tracking=True)
    approver_sequence = fields.Boolean(related="approver_id.approver_sequence")
    automated_sequence = fields.Boolean(related="approver_id.automated_sequence")
    approval_minimum = fields.Integer(related="approver_id.approval_minimum")
    reason = fields.Char('Reason', tracking=True)
    rejection_reason = fields.Text('Rejection Reason', tracking=True, )
    
    # Task Start Approval Fields
    task_start_approver_id = fields.Many2one('res.users', string="Task Start Approver", 
                                           tracking=True)
    task_start_reason = fields.Text('Task Start Rejection Reason', tracking=True)

    state = fields.Selection(selection_add=[
        ('01_in_progress', 'Draft'),
        ('pending', 'To Approve'),
        ('03_approved', 'Pending'),
        ('1_done', 'Completed'),
        ('1_canceled', 'Cancelled'),
        ('start_pending', 'Task Start Pending'),
        ('task_started', 'Task Started'),
        ('start_rejected', 'Start Task Rejected'),
    ], string='Status', index=True, copy=False, default='01_in_progress', tracking=True,
        ondelete={'01_in_progress': 'set default', 'pending': 'set default', '03_approved': 'set default',
                  '1_done': 'set default', '1_canceled': 'set default', 'start_pending': 'set default',
                  'task_started': 'set default', 'start_rejected': 'set default'}
    )

    user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel')
    ], compute="_compute_user_status")

    date_confirmed = fields.Datetime(string="Date Confirmed")

    approver_ids = fields.One2many('task.approval.approver', 'task_id', string="Approvers",
                                   compute='_compute_approver_ids', store=True, readonly=False)

    reference = fields.Char(string="Order Reference", required=True, copy=False,
                            readonly=True, default=lambda self: _("New"))

    post_date = fields.Datetime(string="Post Date", readonly=True)

    @api.model
    def create(self, values):
        if values.get('reference', _('New')) == _('New'):
            values['reference'] = self.env['ir.sequence'].next_by_code('project.task.reference') or _('New')
        res = super(ProjectTask, self).create(values)
        return res

    @api.model
    def _read_group_request_status(self, stages, domain, order):
        request_status_list = dict(self._fields['request_status'].selection).keys()
        return request_status_list

    def send_for_task_start(self):
        """Send task for start approval to manager"""
        self.ensure_one()
        if not self.task_start_approver_id:
            raise UserError(_("Please select a Task Start Approver before sending for approval."))
        
        # Create activity for the task start approver
        self.activity_schedule(
            'odoo_task_approvals.mail_activity_data_task_start_approval',
            user_id=self.task_start_approver_id.id,
            note=_("Task '%s' is waiting for your start approval.") % self.name
        )
        
        self.sudo().write({
            'state': 'start_pending',
            'date_confirmed': fields.Datetime.now()
        })

    def action_approve_task_start(self):
        """Approve task start"""
        self.ensure_one()
        if self.state != 'start_pending':
            raise UserError(_("Task is not in start pending state."))
        
        # Mark activity as done
        self._get_user_task_start_activities(user=self.env.user).action_feedback()
        
        self.sudo().write({
            'state': 'task_started',
            'task_start_reason': False  # Clear any previous rejection reason
        })

    def action_reject_task_start(self, rejection_reason=None):
        """Reject task start"""
        self.ensure_one()
        if self.state != 'start_pending':
            raise UserError(_("Task is not in start pending state."))

        # Mark activity done quietly (no message)
        activities = self._get_user_task_start_activities(user=self.env.user)
        for act in activities:
            act.unlink()  # remove it instead of marking done

        # Update state
        self.sudo().write({
            'state': 'start_rejected',
            'task_start_reason': rejection_reason or _("Task start was rejected by %s") % self.env.user.name
        })

        # Post custom message to chatter
        self.message_post(
            body=_("Task start was rejected by %s. Reason: %s") % (
                self.env.user.name,
                rejection_reason or _("No reason provided.")
            ),
            message_type="comment",
        )

    def _get_user_task_start_activities(self, user):
        """Get task start approval activities for a user"""
        return self.env['mail.activity'].search([
            ('res_model', '=', 'project.task'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('odoo_task_approvals.mail_activity_data_task_start_approval').id),
            ('user_id', '=', user.id)
        ])

    def send_for_approvals(self):
        self.ensure_one()
        if len(self.approver_ids) < self.approval_minimum:
            raise UserError(_("You have to add at least %s approvers to confirm your task.", self.approval_minimum))

        approvers = self.approver_ids
        if self.approver_sequence:
            # If we're restarting the approval process, reset all approvers
            if self.state == '01_in_progress' and any(a.status != 'new' for a in approvers):
                approvers.write({'status': 'new'})
            
            approvers = approvers.filtered(lambda a: a.status in ['new', 'pending', 'waiting'])
            approvers[1:].sudo().write({'status': 'waiting'})
            approvers = approvers[0] if approvers and approvers[0].status != 'pending' else self.env[
                'task.approval.approver']
        else:
            # Handle non-sequential approvals
            # Include canceled approvers when resending for approval
            approvers = approvers.filtered(lambda a: a.status in ['new', 'cancel'])

            # Reset rejection reason and update state
        self.sudo().write({
            'state': 'pending',
            'rejection_reason': False,
            'date_confirmed': fields.Datetime.now(),
            'post_date': fields.Datetime.now(),  # <-- add this line
        })

        # Update approver status and send notifications
        for approver in approvers:
            approver.sudo().write({'status': 'pending'})

            # Send email to portal users, create activity for internal users
            if approver.user_id.has_group('base.group_portal'):
                template = self.env.ref('odoo_task_approvals.mail_template_customer_approval', raise_if_not_found=False)
                if template:
                    template.with_context(mail_post_autofollow=True).send_mail(
                        self.id,
                        force_send=True,
                        email_values={'email_to': approver.user_id.partner_id.email},
                    )
            else:
                approver._create_activity()

    def _update_task_state(self, statuses, required_approved, minimal_approved):
        """Helper method to determine task state based on approvals"""
        if 'cancel' in statuses:
            return '1_canceled'
        elif statuses.count('approved') >= minimal_approved and required_approved:
            return '1_done'
        elif 'approved' in statuses and any(s in ['pending', 'waiting'] for s in statuses):
            return '03_approved'
        elif any(s in ['new', 'pending', 'waiting', 'approved'] for s in statuses):
            return 'pending'
        return '01_in_progress'

    def action_approve(self, approver=None):
        self._ensure_can_approve()
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)

        approver.write({'status': 'approved'})
        # Clear rejection reason when task is approved
        self.write({'rejection_reason': False})
        self._update_next_approvers('pending', approver, only_next_approver=True)
        self._get_user_approval_activities(user=self.env.user).action_feedback()

        for task in self:
            statuses = task.mapped('approver_ids.status')
            required_approved = all(a.status == 'approved' for a in task.approver_ids.filtered('required'))
            minimal_approved = task.approval_minimum if len(statuses) >= task.approval_minimum else len(statuses)

            state = self._update_task_state(statuses, required_approved, minimal_approved)
            task.write({'state': state})

            # Create activity for next approver if in continues approval state
            if state == '03_approved':
                next_approvers = task.approver_ids.filtered(lambda a: a.status == 'pending')
                for approver in next_approvers:
                    if approver.user_id.has_group('base.group_portal'):  # is a portal user (customer)
                        template = self.env.ref('odoo_task_approvals.mail_template_customer_approval')
                        if template:
                            template.with_context(mail_post_autofollow=True).send_mail(
                                task.id,
                                force_send=True,
                                email_values={'email_to': approver.user_id.partner_id.email,}
                            )
                    else:
                        approver._create_activity()

    def action_cancel(self, approver=None, rejection_reason=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        
        # If on_rejection_approval_restart is enabled
        if self.approver_id.on_rejection_approval_restart:
            # Reset all approvers back to their initial state
            self.approver_ids.write({'status': 'new'})
            # Set the first approver to pending
            first_approver = self.approver_ids.sorted(lambda a: a.sequence)[0]
            first_approver.write({'status': 'pending'})
            first_approver._create_activity()
            # Update task state and rejection reason
            self.write({
                'state': 'pending',  # Keep state as pending instead of setting to Draft
                'rejection_reason': rejection_reason or False
            })
            self._get_user_approval_activities(user=self.env.user).action_feedback()
            return
        
        # If to_approve_previous_approver is enabled and there is a previous approver
        elif self.approver_id.to_approve_previous_approver and self.approver_sequence:
            current_approver = approver
            previous_approvers = self.approver_ids.filtered(
                lambda a: a.sequence < current_approver.sequence and a.status == 'approved'
            )
            
            if previous_approvers:
                # Get the most recent previous approver
                previous_approver = previous_approvers.sorted(lambda a: a.sequence, reverse=True)[0]
                # Reset the status of current and subsequent approvers
                self.approver_ids.filtered(
                    lambda a: a.sequence >= current_approver.sequence
                ).write({'status': 'waiting'})
                # Set the previous approver back to pending
                previous_approver.write({'status': 'pending'})
                previous_approver._create_activity()
                # Update task state and rejection reason
                self.write({
                    'state': 'pending',
                    'rejection_reason': rejection_reason or False
                })
                self._get_user_approval_activities(user=self.env.user).action_feedback()
                return
        
        # Default cancellation behavior if no special handling is enabled
        approver.write({'status': 'cancel'})
        self.write({
            'state': '1_canceled',
            'rejection_reason': rejection_reason or False
        })
        self._update_next_approvers('cancel', approver, only_next_approver=False, cancel_activities=True)
        self._get_user_approval_activities(user=self.env.user).action_feedback()

    def action_withdraw(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(lambda a: a.user_id == self.env.user)
        self._update_next_approvers('waiting', approver, only_next_approver=False, cancel_activities=True)
        approver.write({'status': 'pending'})

    def _update_next_approvers(self, new_status, approver, only_next_approver, cancel_activities=False):
        approvers_updated = self.env['task.approval.approver']
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
        activity_type = self.env.ref('odoo_task_approvals.mail_activity_data_approval_task')
        self.activity_ids.filtered(lambda a: a.activity_type_id == activity_type).unlink()

    def _get_user_approval_activities(self, user):
        return self.env['mail.activity'].search([
            ('res_model', '=', 'project.task'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('odoo_task_approvals.mail_activity_data_approval_task').id),
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
            resequence = self.filtered(lambda t: t.approver_sequence and t.state == 'pending')
            for task in resequence:
                if not task.approver_ids.filtered(lambda a: a.status == 'pending'):
                    pending = task.approver_ids.filtered(lambda a: a.status == 'waiting')
                    if pending:
                        pending[0].write({'status': 'pending'})
                        pending[0]._create_activity()
        return res


class TaskApprovalApprover(models.Model):
    _name = 'task.approval.approver'
    _description = 'Task Approver Line'
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

    task_id = fields.Many2one('project.task', string="Task", ondelete='cascade', check_company=True)
    company_id = fields.Many2one(related='task_id.company_id', store=True, readonly=True, index=True)
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
        for approver in self:
            approver.task_id.activity_schedule(
                'odoo_task_approvals.mail_activity_data_approval_task',
                user_id=approver.user_id.id)

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
