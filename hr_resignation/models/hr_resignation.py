# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

RESIGNATION_TYPE = [
    ('resigned', 'Normal Resignation'),
    ('fired', 'Fired by the company')
]


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _description = 'HR Resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    name = fields.Char(string='Order Reference', copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))

    employee_id = fields.Many2one(
        'hr.employee', string="Employee",
        help='Name of the employee for whom the request is creating'
    )

    department_id = fields.Many2one(
        'hr.department', string="Department",
        compute='_compute_department_id', store=False,
        readonly=True,
        help='Department of the employee'
    )

    @api.depends('employee_id')
    def _compute_department_id(self):
        for rec in self:
            if rec.employee_id:
                rec.department_id = rec.employee_id.sudo().department_id.id
            else:
                rec.department_id = False

    resign_confirm_date = fields.Date(
        string="Submitted Date",
        help='Date on which the request is submitted by the employee.',
        tracking=True
    )
    approved_revealing_date = fields.Date(
        string="Approved Last Day Of Employee",
        help='Date on which the request is finally approved.',
        tracking=True
    )
    joined_date = fields.Date(
        string="Join Date",
        help='Joining date of the employee.'
    )

    expected_revealing_date = fields.Date(
        string="Last Day of Employee", required=True,
        help='Employee requested last working day.'
    )

    reason = fields.Text(string="Reason", required=True, help='Specify reason for leaving the company')

    notice_period = fields.Char(string="Notice Period", help="Notice Period of the employee.")
    resignation_type = fields.Selection(selection=RESIGNATION_TYPE)

    change_employee = fields.Boolean(
        string="Change Employee",
        compute="_compute_change_employee",
        help="Checks if the user has permission to change the employee"
    )

    employee_contract = fields.Char(string="Contract")

    # ---------------------------
    # States (Flow)
    # ---------------------------
    state = fields.Selection([
        ('draft', 'Draft'),
        ('dept_manager', 'Department Manager'),
        ('hr_employee', 'HR Employee'),
        ('hr_manager', 'HR Manager'),
        ('payroll', 'Payroll Employee'),
        ('cfo', 'CFO'),
        ('approved', 'Approved'),
        ('cancel', 'Rejected'),
    ], string='Status', default='draft', tracking=True)

    # ---------------------------
    # Approver Users (auto-picked from res.users checkboxes)
    # ---------------------------
    dept_manager_user_id = fields.Many2one('res.users', string='Department Manager (User)', tracking=True)
    hr_employee_user_id = fields.Many2one('res.users', string='HR Employee (User)', tracking=True)
    hr_manager_user_id = fields.Many2one('res.users', string='HR Manager (User)', tracking=True)
    payroll_user_id = fields.Many2one('res.users', string='Payroll Employee (User)', tracking=True)
    cfo_user_id = fields.Many2one('res.users', string='CFO (User)', tracking=True)

    # Button visibility
    show_btn_submit = fields.Boolean(compute='_compute_button_visibility')
    show_btn_dept_manager = fields.Boolean(compute='_compute_button_visibility')
    show_btn_hr_employee = fields.Boolean(compute='_compute_button_visibility')
    show_btn_hr_manager = fields.Boolean(compute='_compute_button_visibility')
    show_btn_payroll = fields.Boolean(compute='_compute_button_visibility')
    show_btn_cfo = fields.Boolean(compute='_compute_button_visibility')

    # ------------------------------------------------
    # No email helpers
    # ------------------------------------------------
    def _silent_write(self, vals):
        return self.with_context(
            tracking_disable=True,
            mail_notrack=True,
            mail_notify_noemail=True,
            mail_auto_subscribe_no_notify=True,
            mail_create_nosubscribe=True,
        ).write(vals)

    def _log_note(self, msg):
        self.ensure_one()
        subtype = self.env.ref('mail.mt_note')
        self.env['mail.message'].sudo().create({
            'model': self._name,
            'res_id': self.id,
            'message_type': 'comment',
            'subtype_id': subtype.id,
            'body': msg,
            'author_id': self.env.user.partner_id.id,
        })

    def _schedule_to_user(self, user, summary):
        self.ensure_one()
        if not user:
            return
        todo = self.env.ref('mail.mail_activity_data_todo')
        self.env['mail.activity'].sudo().create({
            'activity_type_id': todo.id,
            'res_model_id': self.env['ir.model']._get_id(self._name),
            'res_id': self.id,
            'user_id': user.id,
            'summary': summary,
        })

    # ------------------------------------------------
    # Pick role users from checkboxes
    # ------------------------------------------------
    def _get_role_user(self, bool_field):
        return self.env['res.users'].sudo().search([
            (bool_field, '=', True),
            ('active', '=', True)
        ], limit=1)

    def _refresh_approvers_from_users_roles(self):
        vals = {
            'dept_manager_user_id': self._get_role_user('kb_res_dept_manager').id or False,
            'hr_employee_user_id': self._get_role_user('kb_res_hr_employee').id or False,
            'hr_manager_user_id': self._get_role_user('kb_res_hr_manager').id or False,
            'payroll_user_id': self._get_role_user('kb_res_payroll_employee').id or False,
            'cfo_user_id': self._get_role_user('kb_res_cfo').id or False,
        }
        self._silent_write(vals)

    # ------------------------------------------------
    # Permissions / checks
    # ------------------------------------------------
    @api.depends('employee_id')
    def _compute_change_employee(self):
        for rec in self:
            rec.change_employee = self.env.user.has_group('hr.group_hr_user')

    @api.constrains('employee_id')
    def _check_employee_id(self):
        for resignation in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                # Use sudo() to check user_id if access is restricted
                employee = resignation.employee_id.sudo()
                if employee and employee.user_id and employee.user_id.id != self.env.uid:
                    raise ValidationError(_('You cannot create a request for other employees'))

    @api.constrains('employee_id', 'state')
    def _check_duplicate_in_progress(self):
        in_progress_states = ['dept_manager', 'hr_employee', 'hr_manager', 'payroll', 'cfo', 'approved']
        for resignation in self:
            if not resignation.employee_id:
                continue
            # Use sudo search to find other resignations regardless of access rules
            existing = self.sudo().search([
                ('employee_id', '=', resignation.employee_id.id),
                ('id', '!=', resignation.id),
                ('state', 'in', in_progress_states),
            ], limit=1)
            if existing:
                raise ValidationError(
                    _('There is a resignation request already in progress/approved for this employee.'))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if not self.employee_id:
            return

        # Use sudo() to access employee fields if the current user doesn't have access
        employee = self.employee_id.sudo()
        self.joined_date = employee.joining_date or employee.first_contract_date

        contract = self.env['hr.contract'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'open')
        ], limit=1)

        if contract:
            self.employee_contract = contract.name
            self.notice_period = contract.notice_days

    @api.model
    def create(self, vals):
        # sequence
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')

        # ✅ FORCE employee_id from user
        if not vals.get('employee_id'):
            emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
            if not emp:
                raise UserError(_("Your user is not linked to an Employee. Please contact HR."))
            vals['employee_id'] = emp.id

            # Fill joined date + contract details
            vals['joined_date'] = emp.joining_date or emp.first_contract_date
            c = self.env['hr.contract'].sudo().search([('employee_id', '=', emp.id), ('state', '=', 'open')], limit=1)
            if c:
                vals['employee_contract'] = c.name
                vals['notice_period'] = c.notice_days

        # default approvers
        if not vals.get('dept_manager_user_id'):
            vals['dept_manager_user_id'] = self._get_role_user('kb_res_dept_manager').id or False
        if not vals.get('hr_employee_user_id'):
            vals['hr_employee_user_id'] = self._get_role_user('kb_res_hr_employee').id or False
        if not vals.get('hr_manager_user_id'):
            vals['hr_manager_user_id'] = self._get_role_user('kb_res_hr_manager').id or False
        if not vals.get('payroll_user_id'):
            vals['payroll_user_id'] = self._get_role_user('kb_res_payroll_employee').id or False
        if not vals.get('cfo_user_id'):
            vals['cfo_user_id'] = self._get_role_user('kb_res_cfo').id or False

        return super().create(vals)

    def _check_user(self, field_name, expected_state):
        self.ensure_one()
        if self.state != expected_state:
            raise UserError(_("Invalid state for this action."))

        approver = self[field_name]
        if not approver:
            raise UserError(_("Approver is not set. Please enable the approver checkbox on a user."))

        if approver != self.env.user:
            raise UserError(_("Only %s can approve at this stage. You are: %s")
                            % (approver.name, self.env.user.name))

    @api.depends(
        'state',
        'employee_id',
        'dept_manager_user_id', 'hr_employee_user_id', 'hr_manager_user_id', 'payroll_user_id', 'cfo_user_id'
    )
    def _compute_button_visibility(self):
        user = self.env.user
        for rec in self:
            employee_user = rec.employee_id.sudo().user_id
            rec.show_btn_submit = (
                    rec.state == 'draft'
                    and (
                            (rec.employee_id and employee_user == user)
                            or not rec.id  # 👈 NEW: allow before save
                    )
            )

            rec.show_btn_dept_manager = rec.state == 'dept_manager' and rec.dept_manager_user_id == user
            rec.show_btn_hr_employee = rec.state == 'hr_employee' and rec.hr_employee_user_id == user
            rec.show_btn_hr_manager = rec.state == 'hr_manager' and rec.hr_manager_user_id == user
            rec.show_btn_payroll = rec.state == 'payroll' and rec.payroll_user_id == user
            rec.show_btn_cfo = rec.state == 'cfo' and rec.cfo_user_id == user

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Retrieve employee without sudo() to avoid Access Error in the view
        # if the user doesn't have read access to their own employee record.
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)],
            limit=1
        )

        if employee:
            res['employee_id'] = employee.id
            # Use sudo() for reading related data to populate fields
            # since we already have the valid employee record ID.
            emp_sudo = employee.sudo()
            res['joined_date'] = emp_sudo.joining_date or emp_sudo.first_contract_date

            contract = self.env['hr.contract'].sudo().search(
                [('employee_id', '=', employee.id), ('state', '=', 'open')],
                limit=1
            )
            if contract:
                res['employee_contract'] = contract.name
                res['notice_period'] = contract.notice_days

        return res

    # ------------------------------------------------
    # FLOW ACTIONS
    # ------------------------------------------------
    def action_submit_resignation(self):
        self.ensure_one()

        if not self.employee_id:
            raise UserError(_("Employee is missing. Please contact HR to link your user to an employee."))

        if self.joined_date:
            if self.joined_date >= self.expected_revealing_date:
                raise ValidationError(_('Last date of the Employee must be after Joining date'))
        else:
            raise ValidationError(_('Please set a Joining Date for employee'))

        self._refresh_approvers_from_users_roles()

        self._silent_write({
            'state': 'dept_manager',
            'resign_confirm_date': fields.Date.today(),
        })
        self._log_note(_("Resignation submitted by Employee. Sent to Department Manager."))
        self._schedule_to_user(self.dept_manager_user_id, "Resignation: Department Manager Approval")

    def action_dept_manager_approve(self):
        self.ensure_one()
        self._refresh_approvers_from_users_roles()
        self._check_user('dept_manager_user_id', 'dept_manager')

        self._silent_write({'state': 'hr_employee'})
        self._log_note(_("Approved by Department Manager. Sent to HR Employee."))
        self._schedule_to_user(self.hr_employee_user_id, "Resignation: HR Employee Approval")

    def action_hr_employee_approve(self):
        self.ensure_one()
        self._refresh_approvers_from_users_roles()
        self._check_user('hr_employee_user_id', 'hr_employee')

        self._silent_write({'state': 'hr_manager'})
        self._log_note(_("Approved by HR Employee. Sent to HR Manager."))
        self._schedule_to_user(self.hr_manager_user_id, "Resignation: HR Manager Approval")

    def action_hr_manager_approve(self):
        self.ensure_one()
        self._refresh_approvers_from_users_roles()
        self._check_user('hr_manager_user_id', 'hr_manager')

        self._silent_write({'state': 'payroll'})
        self._log_note(_("Approved by HR Manager. Sent to Payroll Employee."))
        self._schedule_to_user(self.payroll_user_id, "Resignation: Payroll Approval")

    def action_payroll_approve(self):
        self.ensure_one()
        self._refresh_approvers_from_users_roles()
        self._check_user('payroll_user_id', 'payroll')

        self._silent_write({'state': 'cfo'})
        self._log_note(_("Approved by Payroll. Sent to CFO."))
        self._schedule_to_user(self.cfo_user_id, "Resignation: CFO Approval")

    def action_cfo_approve(self):
        self.ensure_one()
        self._refresh_approvers_from_users_roles()
        self._check_user('cfo_user_id', 'cfo')

        self._final_approve_resignation()
        self._log_note(_("Approved by CFO. Resignation is Approved."))

    def _final_approve_resignation(self):
        self.ensure_one()

        if not (self.expected_revealing_date and self.resign_confirm_date):
            raise ValidationError(_('Please Enter Valid Dates.'))

        employee_contracts = self.env['hr.contract'].sudo().search([('employee_id', '=', self.employee_id.id)])
        if not employee_contracts:
            raise ValidationError(_("There are no Contracts found for this employee"))

        approved_last_day = self.expected_revealing_date

        for contract in employee_contracts:
            if contract.state == 'open':
                approved_last_day = self.resign_confirm_date + timedelta(days=int(contract.notice_days or 0))
                contract.state = 'cancel'

        self._silent_write({
            'state': 'approved',
            'approved_revealing_date': approved_last_day,
        })

        # Deactivate employee if last day is today/past
        if self.expected_revealing_date <= fields.Date.today() and self.employee_id.active:
            self.employee_id.sudo().write({
                'active': False,
                'resign_date': self.expected_revealing_date,
            })

            if self.resignation_type == 'resigned':
                self.employee_id.sudo().write({'resigned': True})
                departure_reason_id = self.env['hr.departure.reason'].sudo().search([('name', '=', 'Resigned')],
                                                                                    limit=1)
            else:
                self.employee_id.sudo().write({'fired': True})
                departure_reason_id = self.env['hr.departure.reason'].sudo().search([('name', '=', 'Fired')], limit=1)

            running_contract_ids = self.env['hr.contract'].sudo().search([
                ('employee_id', '=', self.employee_id.id),
                ('company_id', '=', self.employee_id.company_id.id),
                ('state', '=', 'open'),
            ])
            running_contract_ids.write({'state': 'close'})

            self.employee_id.sudo().write({
                'departure_reason_id': departure_reason_id.id if departure_reason_id else False,
                'departure_date': self.approved_revealing_date,
            })

            # Deactivate user
            if self.employee_id.user_id:
                linked_user = self.employee_id.user_id.sudo()
                linked_user.write({'active': False})
                self.employee_id.sudo().write({'user_id': False})

    def action_reject_resignation(self):
        self._silent_write({'state': 'cancel'})

    # ------------------------------------------------
    # End of Service Calculation Fields & Methods
    # ------------------------------------------------
    
    # Fields
    total_years = fields.Integer(string="Years", compute="get_total_days")
    total_days = fields.Integer(string="Days", compute="get_total_days")
    total_month = fields.Integer(string="Month", compute="get_total_days")
    total_salary = fields.Float(string="Total wage", readonly=True, compute="get_employee_info")
    total_daily_rates = fields.Float(string="Total Daily Rate", readonly=True, compute="get_employee_dailyrates")
    remaining_days = fields.Integer(string="Remaining Days", readonly=True, compute="get_employee_remaining_days")
    remaining_salary2 = fields.Float(string="Remaining Salary", readonly=True, compute="remaining_salary")

    total_remaining_salary = fields.Float(string="Remaining Salary+Reward", readonly=True, compute="get_remaining_salary")
    total_reward_remaining = fields.Float(string="Total Reward", readonly=True, compute="total_all")
    total_loan = fields.Float(string="Total Loans", readonly=True, compute="get_total_loans")
    clicked = fields.Boolean(string="")
    
    button_set_evacuation = fields.Boolean('Hand over all the covenant to the worker')
    button_set_covenant = fields.Boolean('The act of evading a party for the worker ')
    RewardNotSpecific = fields.Char(string="Service reward")
    RewardSpecific = fields.Char(string="Service reward")
    salary = fields.Integer(string=" salary")
    
    Reward = fields.Integer(string="Reward", compute='total_Reward')
    other = fields.Float(string="Other")
    # notice_period already exists
    notice_period_int = fields.Integer(string="Notice Period (Days)", compute="get_employee_info", store=False)
    total_notice = fields.Float(string="Total Notice Period ", readonly=True, compute="get_total_notice")

    Compensation77 = fields.Float(string="Compensation under Article 77", compute="get_total_Compensation77", readonly=True)

    time_off_remaining_id = fields.Float(string="Remaining time off", readonly=True, compute="action_leave_time")
    time_off_salary_id = fields.Float(string="Remaining salary time off", readonly=True, compute="total_time")
    contract_date_end = fields.Date(string="Real end date of contract")
    type_contract = fields.Selection([
        ('specific', 'specified contract time '),
        ('notspecific', 'None specified contract time'),
        ], string='Type of contract', default='specific')

    specific = fields.Selection([
        ('reason1', 'The expiration of the contract period or the agreement of the two parties to terminate the contract '),
        ('reason2', 'Termination of the contract by the employer'),
        ('reason3', 'Termination of the contract by the employer for one of the cases mentioned in Article 80 '),
        ('reason4', 'Leaving work as a result of force majeure '),
        ('reason5', 'The worker termination of the work contract within six months of the marriage contract or within three months of giving birth'),
        ('reason6', 'The worker leaving work for one of the cases mentioned in Article 81'),
        ('reason7', 'Termination of the contract by the worker or the worker leaving the work in cases other than those mentioned in Article 81'),
        ('reason8', 'Termination of the contract with a valid reason 75'),
        ('reason9', 'Termination of the contract without a valid reason 77'),
    ], string='Reason')

    notspecific = fields.Selection([
        ('reasons1', 'The worker termination of the work contract within six months of the marriage contract or within three months of giving birth'),
        ('reasons2', 'The agreement of the worker and the employer to terminate the contract'),
        ('reasons3', 'The employees resignation'),
        ('reasons4', 'Leaving the worker to work without submitting a resignation other than the cases mentioned in Article 81'),
        ('reasons5', 'The worker left work for one of the cases mentioned in Article 81'),
        ('reasons6', 'Leaving work as a result of force majeure'),
        ('reasons7', 'Termination of the contract by the employer '),
        ('reasons8', 'Termination of the contract by the employer in one of the cases mentioned in Article 80, or during the probation period'),
        ('reason9', 'Termination of the contract with a valid reason 75'),
        ('reason10', 'Termination of the contract without a valid reason 77'),
    ], string='Reason')

    covenant = fields.Selection([
        ('covenantto', 'Covenant delivered'),
        ('notcovenantto', 'Delivery has not been done'),
    ], string='covenant')

    @api.onchange('approved_revealing_date')
    def action_leave_time(self):
        # Accessing employee allocation
        # Warning: allocation_remaining_display might not exist if not added to hr.employee
        # Using sudo() to bypass access rights issues when accessing employee details
        employee = self.employee_id.sudo() if self.employee_id else False
        time_off_remaining = employee.allocation_remaining_display if employee and hasattr(employee, 'allocation_remaining_display') else 0.0
        self.time_off_remaining_id = time_off_remaining

    @api.depends('approved_revealing_date', 'employee_id')
    def get_employee_info(self):
        for rec in self:
            if not rec.employee_id:
                rec.total_salary = 0.0
                rec.contract_date_end = False
                rec.notice_period_int = 0
                continue
            
            # Using sudo() to bypass record rules (e.g., "Employee: own" constraint)
            contract = rec.env['hr.contract'].sudo().search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', 'in', ['open', 'close'])
            ], order='date_start desc', limit=1)

            if contract:
                # Warning: Assuming fields like hra, da, etc exist on hr.contract
                total_wage = contract.wage 
                if hasattr(contract, 'hra'): total_wage += contract.hra
                if hasattr(contract, 'da'): total_wage += contract.da
                if hasattr(contract, 'travel_allowance'): total_wage += contract.travel_allowance
                if hasattr(contract, 'meal_allowance'): total_wage += contract.meal_allowance
                if hasattr(contract, 'medical_allowance'): total_wage += contract.medical_allowance
                if hasattr(contract, 'other_allowance'): total_wage += float(contract.other_allowance)
                
                rec.total_salary = total_wage
                rec.contract_date_end = contract.date_end
                
                if hasattr(contract, 'notice_days'):
                    rec.notice_period_int = contract.notice_days
                else:
                    rec.notice_period_int = 0
            else:
                 rec.total_salary = 0.0
                 rec.contract_date_end = False
                 rec.notice_period_int = 0

    @api.depends('approved_revealing_date')
    def get_total_loans(self):
        for rec in self:
            if rec.employee_id:
                 # Using sudo() to bypass access rights to loans if needed
                loans = rec.env['hr.loan'].sudo().search([('employee_id', '=', rec.employee_id.id),('state','=','approve')])
                loan_amount = 0.0
                if loans:
                    for loan in loans:
                        loan_amount += loan.balance_amount
                rec.total_loan = loan_amount
            else:
                rec.total_loan = 0.0

    @api.onchange('approved_revealing_date', 'total_salary')
    def get_employee_dailyrates(self):
        for rec in self:
            daily_rates = rec.total_salary / 30
            rec.total_daily_rates = daily_rates

    @api.onchange('approved_revealing_date')
    def get_employee_remaining_days(self):
        for rec in self:
            if rec.approved_revealing_date:
                day_count = rec.approved_revealing_date.strftime("%d")
                rec.remaining_days = int(day_count)
            else:
                rec.remaining_days = 0

    @api.onchange('approved_revealing_date', 'total_daily_rates', 'remaining_days', 'Reward')
    def get_remaining_salary(self):
        for rec in self:
            remaining_salary = (rec.total_daily_rates * rec.remaining_days) + rec.Reward
            rec.total_remaining_salary = remaining_salary

    @api.onchange('approved_revealing_date', 'total_daily_rates', 'remaining_days')
    def remaining_salary(self):
        for rec in self:
            remaining_sal = (rec.total_daily_rates * rec.remaining_days)
            rec.remaining_salary2 = remaining_sal
    
    @api.depends('approved_revealing_date', 'joined_date')
    def get_total_days(self):
        for rec in self:
            if rec.joined_date and rec.approved_revealing_date:
                diff = relativedelta(rec.approved_revealing_date, rec.joined_date)
                rec.total_years = diff.years
                rec.total_month = diff.months
                rec.total_days = diff.days
            else:
                rec.total_years = 0
                rec.total_month = 0
                rec.total_days = 0

    @api.depends('notice_period_int', 'total_daily_rates', 'type_contract','specific','notspecific')
    def get_total_notice(self):
        for rec in self:
            if rec.type_contract=='specific':
                if rec.specific == 'reason8':
                    rec.total_notice = rec.notice_period_int * rec.total_daily_rates
                else:
                    rec.total_notice = 0.0  
            else:
                if rec.notspecific == 'reason9':
                    rec.total_notice = rec.notice_period_int * rec.total_daily_rates
                else:
                    rec.total_notice = 0.0  

    @api.depends('Compensation77','type_contract','specific', 'notspecific', 'contract_date_end', 'approved_revealing_date', 'total_salary')
    def get_total_Compensation77(self):
        for rec in self:
            if rec.type_contract=='specific':
                rec.Compensation77 = 0.0
                if rec.specific == 'reason9' and rec.approved_revealing_date and rec.contract_date_end:
                    if rec.contract_date_end > rec.approved_revealing_date:
                        delta_days = (rec.contract_date_end - rec.approved_revealing_date).days
                        daily_salary = rec.total_salary / 30.0
                        rec.Compensation77 = delta_days * daily_salary
            else:
                rec.Compensation77 = 0.0

    @api.onchange('notspecific')
    def function_get_RewardNotSpecifics(self):
        for rec in self:
            if rec.notspecific == 'reasons1':
                rec.RewardNotSpecific = "From the first year to the fifth year, half the salary, after the first five years, the salary for each year"
            elif rec.notspecific == 'reasons2':
                rec.RewardNotSpecific = "From the first year to the fifth year, half the salary, after the first five years, the salary for each year"
            elif rec.notspecific == 'reasons3':
                rec.RewardNotSpecific = "From the second year to the fifth year, one-third of the bonus after the first five years, and a salary for each year "
            elif rec.notspecific == 'reasons4':
                rec.RewardNotSpecific = "Not worth a reward"
            elif rec.notspecific == 'reasons5':
                rec.RewardNotSpecific = "Reserve all rights"
            elif rec.notspecific == 'reasons6':
                rec.RewardNotSpecific = "Reserve all rights"
            elif rec.notspecific == 'reasons7':
                rec.RewardNotSpecific = "From the first year to the fifth year, half the salary, after the first five years, the salary for each year"
            elif rec.notspecific == 'reasons8':
                rec.RewardNotSpecific = "Not worth a reward "

    @api.onchange('specific')
    def function_get_RewardSpecifics(self):
        for rec in self:
            if rec.specific == 'reason1':
                rec.RewardSpecific = "From the first year to the fifth year, half the salary, after the first five years, the salary for each year"
            elif rec.specific == 'reason2':
                rec.RewardSpecific = "From the first year to the fifth year, half the salary, after the first five years, the salary for each year"
            elif rec.specific == 'reason3':
                rec.RewardSpecific = "Not worth a reward"
            elif rec.specific == 'reason4':
                rec.RewardSpecific = "Reserve all rights"
            elif rec.specific == 'reason5':
                rec.RewardSpecific = "From the first year to the fifth year, half the salary, after the first five years, the salary for each year"
            elif rec.specific == 'reason6':
                rec.RewardSpecific = "Reserve all rights"
            elif rec.specific == 'reason7':
                rec.RewardSpecific = "Not worth a reward"
    

    @api.onchange('total_salary', 'type_contract', 'specific', 'notspecific', 'total_years', 'total_month', 'total_days', 'total_daily_rates', 'total_notice')
    def total_Reward(self):
        for rec in self:
            halfsalary = rec.total_salary/2
            if rec.type_contract == 'specific':
                rec.notspecific = ''
                if rec.specific == 'reason3':
                    rec.Reward = 0
                elif rec.specific == 'reason8':
                    # rec.total_notice=rec.notice_period*rec.total_daily_rates # Already computed in get_total_notice
                    if rec.total_years <= 5:
                        rec.Reward = (halfsalary* rec.total_years) + ((halfsalary/ 12)  * rec.total_month ) + (((halfsalary / 12) / 30)  * rec.total_days )+rec.total_notice
                    elif rec.total_years > 5:
                        total5 = (halfsalary*5)
                        anotheryear = rec.total_years - 5
                        totalanother = (rec.total_salary* anotheryear) + ((rec.total_salary/ 12)  * rec.total_month ) + (((rec.total_salary / 12) / 30)  * rec.total_days )
                        rec.Reward = total5 + totalanother + rec.total_notice

                elif rec.specific == 'reason9':
                    if rec.total_years <= 5:
                        rec.Reward = (halfsalary* rec.total_years) + ((halfsalary/ 12)  * rec.total_month ) + (((halfsalary / 12) / 30)  * rec.total_days )
                    elif rec.total_years > 5:
                        total5 = (halfsalary*5)
                        anotheryear = rec.total_years - 5
                        totalanother = (rec.total_salary* anotheryear) + ((rec.total_salary/ 12)  * rec.total_month ) + (((rec.total_salary / 12) / 30)  * rec.total_days )
                        rec.Reward = total5 + totalanother

                else:
                    if rec.total_years < 2:
                        rec.Reward = 0
                    elif rec.total_years <= 5:
                        rec.Reward = (halfsalary* rec.total_years) + ((halfsalary/ 12)  * rec.total_month ) + (((halfsalary / 12) / 30)  * rec.total_days )
                    elif rec.total_years > 5:
                        total5 = (halfsalary*5)
                        anotheryear = rec.total_years - 5
                        totalanother = (rec.total_salary* anotheryear) + ((rec.total_salary/ 12)  * rec.total_month ) + (((rec.total_salary / 12) / 30)  * rec.total_days )
                        rec.Reward = total5 + totalanother
            else:
                rec.specific = ''
                if rec.notspecific == 'reasons3':
                    if rec.total_years < 2:
                        rec.Reward = 0
                    elif rec.total_years <= 5:
                        rec.Reward = (1/3)*((halfsalary* rec.total_years) + ((halfsalary/ 12)  * rec.total_month ) + (((halfsalary / 12) / 30)  * rec.total_days ))
                    elif rec.total_years > 5:
                        total5 = (halfsalary*5)
                        anotheryear = rec.total_years - 5
                        totalanother = ((rec.total_salary* anotheryear) + ((rec.total_salary/ 12)  * rec.total_month ) + (((rec.total_salary / 12) / 30)  * rec.total_days ))
                        rec.Reward = 2/3*(total5 + totalanother)

                elif rec.notspecific == 'reasons8':
                     rec.Reward = 0
                     
                elif rec.notspecific == 'reason9':
                    # rec.total_notice=rec.notice_period_int*rec.total_daily_rates
                    if rec.total_years <= 5:
                        rec.Reward = (halfsalary* rec.total_years) + ((halfsalary/ 12)  * rec.total_month ) + (((halfsalary / 12) / 30)  * rec.total_days )+ rec.total_notice
                    elif rec.total_years > 5:
                        total5 = (halfsalary*5)
                        anotheryear = rec.total_years - 5
                        totalanother = (rec.total_salary* anotheryear) + ((rec.total_salary/ 12)  * rec.total_month ) + (((rec.total_salary / 12) / 30)  * rec.total_days )
                        rec.Reward = total5 + totalanother + rec.total_notice
                elif rec.notspecific == 'reason10':
                    if rec.total_years <= 5:
                        rec.Reward = (halfsalary* rec.total_years) + ((halfsalary/ 12)  * rec.total_month ) + (((halfsalary / 12) / 30)  * rec.total_days )
                    elif rec.total_years > 5:
                        total5 = (halfsalary*5)
                        anotheryear = rec.total_years - 5
                        totalanother = (rec.total_salary* anotheryear) + ((rec.total_salary/ 12)  * rec.total_month ) + (((rec.total_salary / 12) / 30)  * rec.total_days )
                        rec.Reward = total5 + totalanother 
                
                else:
                    if rec.total_years < 2:
                        rec.Reward = 0
                    elif rec.total_years <= 5:
                        rec.Reward = (halfsalary* rec.total_years) + ((halfsalary/ 12)  * rec.total_month ) + (((halfsalary / 12) / 30)  * rec.total_days )
                    elif rec.total_years > 5:
                        total5 = (halfsalary*5)
                        anotheryear = rec.total_years - 5
                        totalanother = (rec.total_salary* anotheryear) + ((rec.total_salary/ 12)  * rec.total_month ) + (((rec.total_salary / 12) / 30)  * rec.total_days )
                        rec.Reward = total5 + totalanother

    @api.onchange('approved_revealing_date', 'total_daily_rates', 'time_off_remaining_id')
    def total_time(self):
        for rec in self:
            time_off_salary = rec.total_daily_rates * rec.time_off_remaining_id
            rec.time_off_salary_id = time_off_salary

    @api.onchange('approved_revealing_date', 'total_remaining_salary', 'time_off_salary_id', 'total_loan', 'other', 'Compensation77')
    def total_all(self):
        for rec in self:
            reward_remaining_salary = (rec.total_remaining_salary + rec.time_off_salary_id) - rec.total_loan + rec.other + rec.Compensation77
            rec.total_reward_remaining = reward_remaining_salary

    # ------------------------------------------------
    # Create Payment Request (Integration with kb_register_payment)
    # ------------------------------------------------
    payment_request_id = fields.Many2one('kb.vender.register.payment', string="Payment Request", readonly=True, copy=False)

    def action_create_payment_request(self):
        self.ensure_one()
        if self.payment_request_id:
            raise ValidationError(_("A payment request is already created."))
        
        if self.total_reward_remaining <= 0:
            raise ValidationError(_("No amount to pay or amount is zero."))
            
        # Try to find partner from employee
        partner = self.employee_id.sudo().user_id.partner_id or self.employee_id.sudo().address_home_id
        if not partner:
            raise ValidationError(_("Employee must have a linked partner (User or Private Address) for payment."))

        # Try to find a default journal (Bank/Cash)
        journal = self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])], limit=1)
        
        # Try to find a payment method (outbound) for this journal
        payment_method_line = False
        if journal:
            payment_method_line = self.env['account.payment.method.line'].search([
                ('journal_id', '=', journal.id),
                ('payment_type', '=', 'outbound')
            ], limit=1)

        vals = {
            'kb_payment_type': 'outbound',
            'kb_CustomerName': partner.id,
            'kb_amount': self.total_reward_remaining,
            'kb_date': fields.Date.today(),
            'kb_memo': _('End of Service: %s') % self.employee_id.name,
            'journal_id': journal.id if journal else False,
            'payment_method_line_id': payment_method_line.id if payment_method_line else False,
            'kb_state': 'draft',
            'move_type': 'entry', 
        }
        
        payment = self.env['kb.vender.register.payment'].create(vals)
        self.payment_request_id = payment.id
        
        return {
            'name': _('Payment Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'kb.vender.register.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }
