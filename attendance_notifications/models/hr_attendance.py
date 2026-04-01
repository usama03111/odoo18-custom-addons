from odoo import models, fields, api, _
import logging
import pytz
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def _send_attendance_email(self, action_type):
        """
        Send email notification for attendance action (check-in or check-out)
        """
        try:
            # Get the appropriate email template based on action type
            if action_type == 'check_in':
                template = self.env.ref('attendance_notifications.email_template_check_in', raise_if_not_found=False)
                template_name = 'Check-in'
                dt_value = self.check_in
            elif action_type == 'check_out':
                template = self.env.ref('attendance_notifications.email_template_check_out', raise_if_not_found=False)
                template_name = 'Check-out'
                dt_value = self.check_out
            else:
                return False

            if not template:
                _logger.warning(f"Email template for {template_name} not found")
                return False

            # Convert datetime to local timezone and format
            local_time_str = ''
            local_time_date = ''
            if dt_value:
                local_dt = Datetime.context_timestamp(self, dt_value)
                local_time_str = local_dt.strftime('%H:%M:%S')
                local_time_date = local_dt.strftime('%d/%m/%Y')

            # Send email to the employee
            if self.employee_id.work_email:
                template.with_context(
                    employee_name=self.employee_id.name,
                    check_time=dt_value,
                    local_time_str=local_time_str,
                    local_time_date=local_time_date,
                    action_type=action_type
                ).send_mail(
                    self.id,
                    force_send=True,
                    email_values={'email_to': self.employee_id.work_email}
                )
                _logger.info(f"{template_name} email sent to {self.employee_id.name} ({self.employee_id.work_email})")
                return True
            else:
                _logger.warning(f"No work email found for employee {self.employee_id.name}")
                return False

        except Exception as e:
            _logger.error(f"Error sending {action_type} email to {self.employee_id.name}: {e}")
            return False

    @api.model
    def create(self, vals):
        """
        Override create method to send check-in email
        """
        attendance = super(HrAttendance, self).create(vals)
        
        # Send check-in email notification
        if attendance:
            attendance._send_attendance_email('check_in')
        
        return attendance

    def write(self, vals):
        """
        Override write method to send check-out email when check_out is set
        """
        result = super(HrAttendance, self).write(vals)
        # Now self is updated, so check for check_out on each record
        if 'check_out' in vals and vals['check_out']:
            for attendance in self:
                if attendance.check_out:
                    attendance._send_attendance_email('check_out')
        return result 