from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    approver_ids = fields.One2many('hr.employee.approver', 'employee_id', string='Approvers')
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string='Approval Status', default='draft', tracking=True)

    def action_submit_approval(self):
        self.ensure_one()
        if not self.approver_ids:
            # If no approvers, auto-approve? Or raise error? 
            # Given requirement "add approvers... when record is created", assuming mandatory.
            raise UserError(_("Please add approvers before submitting."))
        
        self.approval_state = 'pending'
        # Reset all statuses to new if needed, or just set first to pending
        self.approver_ids.write({'status': 'new'})
        
        # Sort by sequence and activate first one
        first_approver = self.approver_ids.sorted('sequence')[0]
        first_approver.status = 'pending'

    def _check_approval_status(self):
        self.ensure_one()
        # Check if current one is approved
        # Find next pending
        # If no next, mark global as approved
        
        # We need to find the *next* approver after the one that just approved.
        # But since we just updated the status of the approver to 'approved' in the calling method,
        # we can just look for the first 'new' one.
        
        next_approvers = self.approver_ids.filtered(lambda a: a.status == 'new').sorted('sequence')
        
        if next_approvers:
            next_approver = next_approvers[0]
            next_approver.status = 'pending'
        else:
            # check if all approved
            if all(a.status == 'approved' for a in self.approver_ids):
                self.approval_state = 'approved'
            # (else edge case: some cancelled? but cancel logic handles that)

    def _handle_rejection(self):
        self.ensure_one()
        self.approval_state = 'cancel'


    user_can_approve = fields.Boolean(compute='_compute_user_can_approve')

    @api.depends('approver_ids.status', 'approver_ids.user_id')
    def _compute_user_can_approve(self):
        for employee in self:
            # Find the pending approver
            pending_approver = employee.approver_ids.filtered(lambda a: a.status == 'pending')
            # Check if current user is that approver
            if pending_approver and pending_approver.user_id == self.env.user:
                employee.user_can_approve = True
            else:
                employee.user_can_approve = False

    def action_approve_step(self):
        self.ensure_one()
        approver = self.approver_ids.filtered(lambda a: a.status == 'pending' and a.user_id == self.env.user)
        if not approver:
             raise UserError(_("You are not the current approver."))
        approver.action_approve()
    
    def action_reject_step(self):
        self.ensure_one()
        approver = self.approver_ids.filtered(lambda a: a.status == 'pending' and a.user_id == self.env.user)
        if not approver:
             raise UserError(_("You are not the current approver."))
        approver.action_cancel()
