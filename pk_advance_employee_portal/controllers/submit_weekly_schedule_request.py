from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class PortalWeeklyRequest(CustomerPortal):

    @http.route(['/weekly-schedule/new'], type='http', auth="user", website=True)
    def portal_weekly_schedule_form(self, **kw):
        return request.render("pk_advance_employee_portal.weekly_schedule__template", {})

    @http.route(['/weekly-schedule/request'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_weekly_schedule_submit(self, **post):
        resource_id = post.get('resource_id')
        start_datetime = post.get('start_datetime')
        end_datetime = post.get('end_datetime')
        role_id = post.get('role_id')
        company_id = post.get('company_id')

        employee = request.env.user.employee_id

        if employee:
            request.env['planning.slot'].sudo().create({
                'employee_id': employee.id,
                'resource_id': int(resource_id),
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'role_id': int(role_id),
                'company_id': int(company_id),
            })

        return request.redirect('/weekly/schedule')

