from importlib.resources import _

from odoo import http
from odoo.http import route, request
from odoo.addons.portal.controllers import portal


class ProjectTaskPortal(portal.CustomerPortal):


    #redirect the odoo standard project and task routs to our custom
    @http.route(['/my/projects', '/my/tasks'], type='http', auth='user', website=True)
    def block_default_routes(self, **kw):
        return request.redirect('/tasks/my')

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "project_checkout_count" in counters:
            count = request.env["project.task"].search_count([])
            values["project_checkout_count"] = count
        return values

    @route(["/tasks/my", "/tasks/my/page/<int:page>"], type="http", auth="user", website=True)
    def portal_project_tasks_view(self, page=1, **kw):
        Task = request.env["project.task"].sudo()
        user_id = request.env.uid

        # fields on which to filter
        search_input_values = {
            'project_id': {'input': 'project_id', 'label': _('Search by Project'), 'order': 1},
            'task_id': {'input': 'task_id', 'label': _('Search by Task'), 'order': 2},
            'assignee': {'input': 'user_ids', 'label': _('Search by Assignee'), 'order': 3},
            'milestone': {'input': 'milestone_id', 'label': _('Search by Milestone'), 'order': 4},
        }

        search_in = request.params.get('search_in', 'project_id')
        search_value = request.params.get('search', '').strip()

        # Base domain for user
        domain = [('user_ids', 'in', [user_id])]

        # Apply search filter
        if search_value:
            if search_in == 'project_id':
                domain += [('project_id.name', 'ilike', search_value)]
            elif search_in == 'task_id':
                domain += [('name', 'ilike', search_value)]
            elif search_in == 'assignee':
                domain += [('user_ids.name', 'ilike', search_value)]
            elif search_in == 'milestone':
                domain += [('milestone_id.name', 'ilike', search_value)]
            else:
                # Default fallback
                domain += ['|', ('name', 'ilike', search_value), ('project_id.name', 'ilike', search_value)]

        task_count = Task.search_count(domain)
        pager_data = portal.pager(url="/tasks/my", total=task_count, page=page, step=self._items_per_page)

        tasks = Task.search(domain, limit=self._items_per_page, offset=pager_data['offset'])

        values = self._prepare_portal_layout_values()
        values.update({
            "checkouts": tasks,
            "page_name": "project_tasks",
            "default_url": "/tasks/my",
            "pager": pager_data,
            "user": request.env.user,
            "search_input_values": search_input_values,
            "search_in": search_in,
            "search": search_value,
        })
        return request.render("pk_advance_employee_portal.project_tasks_temp_id", values)
