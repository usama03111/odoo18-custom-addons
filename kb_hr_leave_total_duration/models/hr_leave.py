from odoo import models, fields, api
from odoo.addons.resource.models.utils import HOURS_PER_DAY

class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    is_calendar_days = fields.Boolean(string="Count Total Days", default=False)

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        """
            Compute leave duration in days and hours.

            If 'is_calendar_days' is enabled, the duration is calculated as
            pure calendar days (inclusive of start and end dates),
            ignoring the working schedule from the resource calendar.

            Otherwise, fallback to the standard Odoo duration calculation.
            """
        result = super()._get_durations(check_leave_type=check_leave_type, resource_calendar=resource_calendar)
        for leave in self:
            if leave.is_calendar_days and leave.request_date_from and leave.request_date_to:
                days = (leave.request_date_to - leave.request_date_from).days + 1
                hours = days * HOURS_PER_DAY
                result[leave.id] = (days, hours)
        return result
