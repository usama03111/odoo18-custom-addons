from odoo import http
from odoo.http import route, request
from odoo.addons.portal.controllers import portal


class WeeklyCustomerPortal(portal.CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "weekly_checkout_count" in counters:
            count = request.env["planning.slot"].search_count([])
            values["weekly_checkout_count"] = count
        return values

    @route(["/weekly/schedule", "/weekly/schedule/page/<int:page>"],type="http", auth="user", website=True, )
    def portal_weekly_form_view(self, page=1, **kw):
        checkout = request.env["planning.slot"].sudo()

        domain = [('employee_id.user_id', '=', request.env.uid),('state', '=', 'published')]

        # Prepare pager data
        checkout_count = checkout.search_count(domain)
        pager_data = portal.pager(
            url="/weekly/schedule",
            total=checkout_count,
            page=page,
            step=self._items_per_page,
        )
        # Recordset according to pager and domain filter
        checkouts = checkout.search(domain, limit=self._items_per_page, offset=pager_data["offset"], )
         # Prepare template values and render
        values = self._prepare_portal_layout_values()

        values.update({"checkouts": checkouts,
                       "page_name": "weekly_schedule",
                       "default_url": "/weekly/schedule",
                       "pager": pager_data,
                       "user": request.env.user})
        return request.render("pk_advance_employee_portal.weekly_schedule_form_view_temp_id", values)

    @http.route(["/weekly/schedule/form/<model('hr.leave'):leave_id>"],type="http", auth="user", website=True)
    def portal_weekly_list_view(self, leave_id, **kw):
        vals = {'doc':leave_id, "user": request.env.user}
        return request.render("pk_advance_employee_portal.weekly_schedule_form_view_temp_id", vals)
