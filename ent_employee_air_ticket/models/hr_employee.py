from datetime import date
from odoo import fields, models
from odoo.tools.float_utils import float_round
from odoo.addons.resource.models.utils import HOURS_PER_DAY

class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    air_ticket_display = fields.Char(compute='_compute_allocation_remaining_display')
    air_ticket_remaining_display = fields.Char(compute='_compute_allocation_remaining_display')
    paid_time_off_display = fields.Char(compute='_compute_allocation_remaining_display')
    paid_time_off_remaining_display = fields.Char(compute='_compute_allocation_remaining_display')

    def _compute_allocation_remaining_display(self):
        super()._compute_allocation_remaining_display()
        current_date = date.today()
        allocations = self.env['hr.leave.allocation'].search([('employee_id', 'in', self.ids)])
        
        if not allocations:
            for employee in self:
                employee.air_ticket_remaining_display = "0"
                employee.air_ticket_display = "0"
                employee.paid_time_off_remaining_display = "0"
                employee.paid_time_off_display = "0"
            return
            
        leaves_taken = self._get_consumed_leaves(allocations.holiday_status_id)[0]
        
        for employee in self:
            air_ticket_remaining = 0
            air_ticket_max = 0
            paid_time_off_remaining = 0
            paid_time_off_max = 0
            
            if employee in leaves_taken:
                for leave_type in leaves_taken[employee]:
                    if leave_type.requires_allocation == 'no' or not leave_type.show_on_dashboard:
                        continue
                    for allocation in leaves_taken[employee][leave_type]:
                        if allocation and allocation.date_from <= current_date\
                                and (not allocation.date_to or allocation.date_to >= current_date):
                            virtual_remaining_leaves = leaves_taken[employee][leave_type][allocation]['virtual_remaining_leaves']
                            
                            days_rem = virtual_remaining_leaves\
                                if leave_type.request_unit in ['day', 'half_day']\
                                else virtual_remaining_leaves / (employee.resource_calendar_id.hours_per_day or HOURS_PER_DAY)
                                
                            if getattr(allocation, 'is_air_ticket', False):
                                air_ticket_remaining += days_rem
                                air_ticket_max += allocation.number_of_days
                            else:
                                paid_time_off_remaining += days_rem
                                paid_time_off_max += allocation.number_of_days
                            
            employee.air_ticket_remaining_display = "%g" % float_round(air_ticket_remaining, precision_digits=2)
            employee.air_ticket_display = "%g" % float_round(air_ticket_max, precision_digits=2)
            employee.paid_time_off_remaining_display = "%g" % float_round(paid_time_off_remaining, precision_digits=2)
            employee.paid_time_off_display = "%g" % float_round(paid_time_off_max, precision_digits=2)
