from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployeeApprover(models.Model):
    _name = 'hr.employee.approver'
    _description = 'Employee Approver'
    _order = 'sequence, id'

    employee_id = fields.Many2one('hr.employee', string='Employee', ondelete='cascade', required=True)
    user_id = fields.Many2one('res.users', string='Approver', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Valided'),
    ], string='Status', default='new', readonly=True)

    def action_approve(self):
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("You can only approve pending requests."))
        self.status = 'approved'
        self.employee_id._check_approval_status()

    def action_cancel(self):
        self.ensure_one()
        # if self.status != 'pending':
        #     raise UserError(_("You can only reject pending requests."))
        self.status = 'cancel'
        self.employee_id._handle_rejection()
