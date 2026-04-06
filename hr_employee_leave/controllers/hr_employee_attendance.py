from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager



class HrEmployeeLeave(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'employee_attendance_count' in counters:
            attendance_count = request.env['hr.leave'].search_count([])
            values['employee_attendance_count'] = attendance_count
        return values

    def _get_attendance_domain(self):
        return [('employee_id.user_id', '=', request.env.uid)]

    @http.route(['/employee/leaves'], type='http', auth='user', website=True)
    def employee_leave_list(self, page=1, view='table', **kw):
        employee = request.env.user.employee_id.sudo()
        Attendance = request.env['hr.attendance'].sudo()
        domain = self._get_attendance_domain()

        total = Attendance.search_count(domain)

        pager = portal_pager(
            url='/employee/leaves',
            url_args={'view': view},
            total=total,
            page=page,
            step=10,
        )

        records = Attendance.search(
            domain,
            limit=10,
            offset=pager['offset'],
            order='check_in desc'
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'records': records,
            'pager': pager,
            'page_name': 'employee_leave_list',
            'view_type': view,   # table / kanban
            'attendance_state': employee.attendance_state,
        })

        template = ('hr_employee_leave.hr_employee_leave_list_template' )

        return request.render(template, values)

    @http.route(
        ['/employee/leave/<model("hr.attendance"):attendance>'],
        type='http', auth='user', website=True
    )
    def employee_leave_form(self, attendance, **kw):

        #  Portal access rule
        if attendance.employee_id.user_id.id != request.env.uid:
            return request.redirect('/employee/leaves')

        values = self._prepare_portal_layout_values()
        values.update({
            'attendance': attendance,
            'page_name': 'employee_leave_form',
        })

        return request.render(
            'hr_employee_leave.hr_employee_leave_form_template',
            values
        )

    @http.route(
        '/employee/attendance/toggle',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=True
    )
    def portal_attendance_toggle(self, **kw):

        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')

        # IMPORTANT: sudo is required in portal
        employee.sudo()._attendance_action_change()

        return request.redirect('/employee/leaves')
