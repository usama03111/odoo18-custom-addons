from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class PortalLeaveRequest(CustomerPortal):

    @http.route(['/my/leaves/new'], type='http', auth="user", website=True)
    def portal_leave_create_form(self, **kw):
        return request.render("pk_advance_employee_portal.portal_leave_create_template", {})

    @http.route(['/my/leaves/create'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_leave_create_submit(self, **post):
        leave_type_id = post.get('leave_type')
        date_from = post.get('request_date_from')
        date_to = post.get('request_date_to')
        reason = post.get('reason')

        employee = request.env.user.employee_id

        if employee and leave_type_id:
            request.env['hr.leave'].sudo().create({
                'employee_id': employee.id,
                'holiday_status_id': int(leave_type_id),
                'request_date_from': date_from,
                'request_date_to': date_to,
                'date_from': date_from,
                'date_to': date_to,
                'name': reason or "Leave Request from Portal",
            })

        return request.redirect('/employee/leaves')

