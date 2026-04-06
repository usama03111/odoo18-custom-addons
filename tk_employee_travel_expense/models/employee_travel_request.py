# -*- coding: utf-8 -*-
from datetime import date
from datetime import timedelta
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class EmployeeTravelRequest(models.Model):
    """
    Manages employee travel request details.

    Handles creating, updating, approving, and summarizing travel requests,
    including destination, purpose, dates, estimated expenses, and status.
    """
    _name = 'employee.travel.request'
    _description = 'Employee Travel Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'


    sequence = fields.Char(default="New", tracking=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  default=lambda self: self.env.user.employee_id.id, tracking=True)
    department_id = fields.Many2one('hr.department',
                                    default=lambda self: self.env.user.employee_id.department_id.id,
                                    string="Department", tracking=True)
    manager_id = fields.Many2one('res.users',string="Manager", tracking=True)
    request_date = fields.Date(string="Create Date",
                               default=date.today(), tracking=True)
    confirm_date = fields.Date(string="Confirmed Date", tracking=True)
    approve_date = fields.Date(string="Approved Date", tracking=True)
    request_by = fields.Many2one('res.users', string="Create By",
                                 default=lambda self: self.env.user.id, tracking=True)
    confirm_by = fields.Many2one('res.partner', string="Confirmed By", tracking=True)
    approve_by = fields.Many2one('res.partner', string="Approved By", tracking=True)
    company_id = fields.Many2one('res.company',
                                 string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('approve', 'Approved'), ('rejected', 'Rejected'),
                              ('expenses_submitted', 'Expenses Completed')], default='draft', tracking=True)

    # Travel Information
    travel_information = fields.Char(string="Title")
    project_id = fields.Many2one('project.project')

    # Employee Travel Details
    from_street = fields.Char()
    from_street2 = fields.Char()
    from_city = fields.Char()
    from_zip = fields.Char()
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', domain="[('country_id', '=?', country_id)]")
    to_street = fields.Char()
    to_street2 = fields.Char()
    to_city = fields.Char()
    to_state_id = fields.Many2one('res.country.state', domain="[('country_id', '=?', to_country_id)]")
    to_zip = fields.Char()
    to_country_id = fields.Many2one('res.country')
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    mobile = fields.Char(string="Mobile")
    request_departure_date = fields.Date(string="Departure Date")
    travel_mode_id = fields.Many2one('departure.mode', string="Mode of Travel")
    request_return_date = fields.Date(string="Return Date")
    trip_days = fields.Float(string="Days", compute="_compute_trip_days")
    expense_count = fields.Char(readonly=True, compute='_compute_count_employee_expenses')
    request_reject_reason = fields.Char(string="Reject Reason")
    closing_notes = fields.Text(string="Closing Notes")

    # Other Information
    departure_mode_id = fields.Many2one('departure.mode', string="Departure Mode")
    visa_agent = fields.Many2one('res.partner', string="Visa Agent")
    return_departure_mode_id = fields.Many2one('departure.mode', string="Return Mode")
    ticket_booking_agent = fields.Many2one('res.partner', string="Ticket Booking Agent")
    is_advance_payment = fields.Boolean(string="Advance Payment")

    # Accounting
    bank_id = fields.Many2one('res.bank')
    cheque_no = fields.Char(string="Cheque No.")

    # Advance Payment Register
    date = fields.Date(string="Date", default=date.today(), )
    product_id = fields.Many2one('product.product', domain="[('type', '!=', 'service')]", string="Product")
    description = fields.Char(string="Description")
    unit_price = fields.Monetary(string="Unit Price", currency_field='currency_id')
    quantity = fields.Float(string="Quantity", default=1)
    sub_total = fields.Monetary(string="Subtotal", currency_field='currency_id',
                                compute="_compute_sub_total", store=True)
    expense_sheet = fields.Selection([
        ('single_line', 'Expense wise Report'),
        ('multiple_line', 'Combine Expense Report'),
    ], string="Expense Report")
    # Expense
    expense_ids = fields.One2many('hr.expense', 'employee_travel_expense_id')
    expense_total = fields.Monetary(string="Expense Total", compute="_compute_expense_total",
                                    currency_field='currency_id')
    approve_expense_total = fields.Monetary(string="Approve Expense Total",
                                            compute="_compute_approve_expense_total", currency_field='currency_id')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence') or vals['sequence'] == _('New'):
                vals['sequence'] = (self.env['ir.sequence']
                                .next_by_code('employee.travel.request') or _('New'))
        return super().create(vals_list)


    def action_request_confirm(self):
        """
        Confirm the request by changing its stage and scheduling a manager To-Do activity.
        """
        self.write({
            'confirm_by': self.env.user.partner_id.id,
            'confirm_date': date.today(),
            'state': 'confirm'
        })
        # Schedule an activity
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=fields.Date.today() + timedelta(days=2),
            summary='Approval Needed: Travel Request',
            note=(
                f"The travel request <b>{self.sequence}</b> was created by "
                f"<b>{self.request_by.name}</b> on "
                f"<b>{self.request_date.strftime('%Y-%m-%d')}</b>. "
                f"Please review and approve the request."
            ),
            user_id=self.manager_id.user_id.id,
        )

    def action_request_approve(self):
        """
        Approve the employee's request by updating the stage and logging the approval.
        """
        self.write({
            'approve_by': self.env.user.partner_id.id,
            'approve_date': date.today(),
            'state': 'approve'
        })
        self.message_post(
            body="Travel request has been Approved.",
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

    def action_request_rejected(self):
        """
        Trigger the rejection workflow by returning an action to capture the rejection reason.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Reject Reason',
            'view_mode': 'form',
            'res_model': 'travel.request.reject.reason',
            'target': 'new',
        }

    def action_request_expenses_submitted(self):
        """
         Mark the request as 'Expenses Submitted' by updating its stage.
         Throws the error if expense sheet report is not selected.
        """
        if not self.expense_ids:
            raise UserError("Expense is not created please create the expense.")

        self.state = 'expenses_submitted'

    def action_request_draft(self):
        """
        Mark the request as 'Draft' by updating its stage.
        Remove the data of confirm_by and confirm_date.
        """
        self.write({
            'confirm_by': False,
            'confirm_date': False,
            'state': 'draft'
        })

    def action_add_expense(self):
        """
        This method is used to initiate the creation of an
        expense linked to the current travel request.
        It opens the expense form view with default values set
        for the employee_id,employee_travel_request_id,payment_mode fields.
        Throws the user error if expense_sheet is not selected.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'view_mode': 'form,list',
            'context': {
                'default_employee_travel_expense_id': self.id,
                'default_employee_id': self.employee_id.id,
                'default_payment_mode': 'own_account',
            }
        }

    def employee_expenses_action(self):
        """
        Trigger the action which shows the expense which have the employee_travel_request_id.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'view_mode': 'list,form',
            'domain': [('employee_travel_expense_id', '=', self.id)],
        }

    def _compute_count_employee_expenses(self):
        """
        Return an action showing expenses linked to the current travel request.
        """
        for record in self:
            record.expense_count = record.env['hr.expense'].search_count([
                ('employee_travel_expense_id', '=', record.id)
            ])

    @api.depends('request_departure_date', 'request_return_date')
    def _compute_trip_days(self):
        """
        Compute the number of trip days based on the departure and return dates.
        """
        for record in self:
            if record.request_departure_date and record.request_return_date:
                delta = record.request_return_date - record.request_departure_date
                record.trip_days = delta.days + 1 if delta.days >= 0 else 0
            else:
                record.trip_days = 0

    @api.depends('unit_price', 'quantity')
    def _compute_sub_total(self):
        for record in self:
            record.sub_total = record.unit_price * record.quantity

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """
        Clear the state when the country is changed and does not match the state’s country.
        """
        for record in self:
            if record.country_id and record.country_id != record.state_id.country_id:
                record.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        """
        Automatically update the country based on the selected state.
        """
        for record in self:
            if record.state_id.country_id:
                record.country_id = record.state_id.country_id

    @api.onchange('to_country_id')
    def _onchange_to_country_id(self):
        """
        Clear the state when the to_country is changed and does not match the state’s country.
        """
        for record in self:
            if record.to_country_id and record.to_country_id != record.to_state_id.country_id:
                record.to_state_id = False

    @api.onchange('to_state_id')
    def _onchange_to_state(self):
        """
        Automatically update the to_country based on the selected to_state.
        """
        for record in self:
            if record.to_state_id.country_id:
                record.to_country_id = record.to_state_id.country_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Automatically update the record  based on the selected employee_id.
        """
        for records in self:
            records.department_id = records.employee_id.department_id.id
            records.phone = records.employee_id.work_phone
            records.mobile = records.employee_id.mobile_phone
            records.email = records.employee_id.work_email

    def _compute_expense_total(self):
        """
        Automatically calculate the expenses total.
        """
        for records in self:
            expense_total = 0.0
            if records.expense_ids:
                for expense in records.expense_ids:
                    expense_total += expense.total_amount_currency
            records.expense_total = expense_total

    def _compute_approve_expense_total(self):
        """
        Automatically calculate the expenses total which is paid.
        """
        for records in self:
            expense_total = 0.0
            if records.expense_ids:
                for expense in records.expense_ids:
                    if expense.state == 'done':
                        expense_total += expense.total_amount_currency
            records.approve_expense_total = expense_total




class DepartureMode(models.Model):
    """
    Represents the mode of departure for travel.
    """
    _name = 'departure.mode'
    _description = 'Departure Mode'
    _rec_name = 'departure_mode'

    departure_mode = fields.Char(string="Travel Modes", required=True)
