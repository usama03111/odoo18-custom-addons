# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo import _, api, fields, models


class HrLeaveAllocationGenerateMultiWizard(models.TransientModel):
    _inherit = "hr.leave.allocation.generate.multi.wizard"

    type_request_unit = fields.Selection([
        ('hour', 'Hours'),
        ('half_day', 'Half Day'),
        ('day', 'Day'),
    ], compute="_compute_type_request_unit")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_request_unit(self):
        """Mirror logic from hr.leave.allocation._get_request_unit."""
        self.ensure_one()
        if self.allocation_type == "accrual" and self.accrual_plan_id:
            return self.accrual_plan_id.sudo().added_value_type
        elif self.allocation_type == "regular":
            return self.holiday_status_id.request_unit
        return "day"

    @api.depends("allocation_type", "holiday_status_id", "accrual_plan_id")
    def _compute_type_request_unit(self):
        for wizard in self:
            wizard.type_request_unit = wizard._get_request_unit()

    # ------------------------------------------------------------------
    # Computed name — react to accrual_plan_id changes as well
    # ------------------------------------------------------------------

    @api.depends('holiday_status_id', 'duration', 'allocation_type', 'accrual_plan_id')
    def _compute_name(self):
        for wizard in self:
            wizard.name = wizard._get_title()

    def _get_title(self):
        self.ensure_one()
        if not self.holiday_status_id:
            return _("Allocation Request")
        unit = self.type_request_unit or self.request_unit or 'day'
        return _(
            '%(name)s (%(duration)s %(unit)s(s))',
            name=self.holiday_status_id.name,
            duration=self.duration,
            unit=unit,
        )

    # ------------------------------------------------------------------
    # Pick a representative employee for the accrual simulation
    # ------------------------------------------------------------------

    def _get_simulation_employee(self):
        """Return a single employee to use for the accrual simulation preview."""
        self.ensure_one()
        if self.allocation_mode == 'employee' and self.employee_ids:
            return self.employee_ids[0]
        if self.allocation_mode == 'department' and self.department_id:
            emp = self.department_id.member_ids[:1]
            if emp:
                return emp
        if self.allocation_mode == 'category' and self.category_id:
            emp = self.category_id.employee_ids.filtered(
                lambda e: e.company_id in self.env.companies
            )[:1]
            if emp:
                return emp
        # By Company fallback — any employee in the company
        return self.env['hr.employee'].search(
            [('company_id', '=', self.company_id.id)], limit=1
        )

    # ------------------------------------------------------------------
    # Simulate accrual days (mirrors _onchange_date_from in hr.leave.allocation)
    # ------------------------------------------------------------------

    def _simulate_accrual_duration(self):
        """
        Run a dry accrual simulation using a temporary hr.leave.allocation record
        (never stored) and return the computed number_of_days.
        Returns 0.0 if no representative employee is found.
        """
        self.ensure_one()
        if not self.accrual_plan_id or not self.date_from:
            return 0.0

        employee = self._get_simulation_employee()
        if not employee:
            return 0.0

        date_to = min(self.date_to, date.today()) if self.date_to else False

        fake = self.env['hr.leave.allocation'].new({
            'holiday_status_id': self.holiday_status_id.id,
            'allocation_type': 'accrual',
            'accrual_plan_id': self.accrual_plan_id.id,
            'employee_id': employee.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'state': 'confirm',
            'number_of_days': 0,
            'lastcall': self.date_from,
            'nextcall': False,
            'already_accrued': False,
            'carried_over_days_expiration_date': False,
            'expiring_carryover_days': 0,
        })
        fake.sudo()._process_accrual_plans(date_to, log=False)
        result = float(fake.number_of_days)
        fake.invalidate_recordset()
        return result

    # ------------------------------------------------------------------
    # Onchange: sync wizard fields when allocation_type / plan / date change
    # ------------------------------------------------------------------

    @api.onchange('allocation_type', 'accrual_plan_id', 'date_from', 'date_to',
                  'employee_ids', 'allocation_mode')
    def _onchange_accrual_fields(self):
        if self.allocation_type == 'accrual':
            # Auto-fill Time Off Type from accrual plan when the plan is bound
            if self.accrual_plan_id and self.accrual_plan_id.time_off_type_id:
                self.holiday_status_id = self.accrual_plan_id.time_off_type_id

            # Simulate accrual to show estimated days (same as single-employee form)
            self.duration = self._simulate_accrual_duration()
        else:
            # Regular allocation: default to 1 day if nothing entered
            if not self.duration:
                self.duration = 1.0
