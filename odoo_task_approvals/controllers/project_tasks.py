# from importlib.resources import

from odoo import http, _
from odoo.http import route, request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import CustomerPortal

class ProjectTaskPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "project_checkout_count" in counters:
            # Only count tasks where the user is an approver and task needs their action
            count = request.env["project.task"].sudo().search_count([
                ('approver_ids.user_id', '=', request.env.user.id),
            ])
            values["project_checkout_count"] = count
        return values

class ProjectTask(http.Controller):

    @route(["/tasks/my", "/tasks/my/page/<int:page>"], type="http", auth="user", website=True)
    def portal_project_tasks_kanban(self, page=1, **kw):
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

        # Base domain for user - show tasks where user is an approver
        # domain = [
        #     ('approver_ids.user_id', '=', user_id),
        #     ('state', 'in', ['pending', '03_approved','1_canceled','1_done'])
        # ]
        domain = [
            ('approver_ids.user_id', '=', user_id),]

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
                domain += ['|', ('name', 'ilike', search_value), ('project_id.name', 'ilike', search_value)]

        task_count = Task.search_count(domain)
        pager_data = portal.pager(url="/tasks/my", total=task_count, page=page, )

        tasks = Task.search(domain, offset=pager_data['offset'] ,  order="create_date desc")
        values = {}
        values.update({
            "tasks": tasks,
            "page_name": "project_tasks_kanban_templ_id",
            "default_url": "/tasks/my",
            "pager": pager_data,
            "user": request.env.user,
            "search_input_values": search_input_values,
            "search_in": search_in,
            "search": search_value,
        })
        return request.render("odoo_task_approvals.project_tasks_kanban_templ_id", values)

    @route(["/table/tasks/my", "/tasks/my/page/<int:page>"], type="http", auth="user", website=True)
    def portal_project_tasks_table(self, page=1, **kw):
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

        # Base domain for user - show tasks where user is an approver
        # i have added domain to show cancel task and done
        domain = [
            ('approver_ids.user_id', '=', user_id),]

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
                domain += ['|', ('name', 'ilike', search_value), ('project_id.name', 'ilike', search_value)]

        task_count = Task.search_count(domain)
        pager_data = portal.pager(url="/table/tasks/my", total=task_count, page=page, )

        tasks = Task.search(domain,  offset=pager_data['offset'], order="create_date desc")
        # values = self._prepare_portal_layout_values()
        values = {}
        values.update({
            "tasks": tasks,
            "page_name": "project_tasks_table_temp_id",
            "default_url": "/table/tasks/my",
            "pager": pager_data,
            "user": request.env.user,
            "search_input_values": search_input_values,
            "search_in": search_in,
            "search": search_value,
        })
        return request.render("odoo_task_approvals.project_tasks_table_temp_id", values)

    @http.route("/task/project/<model('project.task'):name>/", auth="user", website=True)
    def display_project_task_detail(self, name,view=None):
        # Get the selection dictionary for the state field
        state_selection = name.fields_get()['state']['selection']
        state_label = dict(state_selection).get(name.state, name.state)
        
        # Check if current user can approve/reject
        current_approver = name.approver_ids.filtered(lambda a: a.user_id == request.env.user)
        can_approve = current_approver and current_approver.status == 'pending'
        
        # If sequential approval, check if it's user's turn
        if name.approver_sequence:
            pending_approvers = name.approver_ids.filtered(lambda a: a.status == 'pending')
            can_approve = can_approve and (pending_approvers[0].user_id == request.env.user if pending_approvers else False)

        vals = {
            "name": name,
            "state_label": state_label,
            "page_name": "portal_form_view",
            "can_approve": can_approve,
            'origin_view': view,
            "current_approver": current_approver,
        }
        return request.render("odoo_task_approvals.task_project_portal_form_view", vals)

    @http.route('/task/project/<int:task_id>/accept', auth="user", website=True, csrf=False)
    def project_task_accept(self, task_id):
        task = request.env['project.task'].sudo().browse(task_id)
        if task.exists():
            approver = task.approver_ids.filtered(lambda a: a.user_id == request.env.user)
            if approver and approver.status == 'pending':
                task.sudo().action_approve(approver)
        return request.redirect(f"/task/project/{task_id}/")

    @http.route('/task/project/<int:task_id>/reject/form', auth="user", website=True)
    def portal_task_reject_form(self ,task_id):
        task = request.env['project.task'].sudo().browse(task_id)
        if not task.exists():
            return request.redirect('/my')
            
        values = {
            'task': task,
            'page_name': 'task_rejection',

        }
        return request.render("odoo_task_approvals.task_rejection_form", values)

    @http.route('/task/project/<int:task_id>/reject/submit', auth="user", website=True, methods=['POST'])
    def portal_task_reject_submit(self, task_id, **kw):
        task = request.env['project.task'].sudo().browse(task_id)
        if task.exists():
            rejection_reason = kw.get('rejection_reason', '').strip()
            if rejection_reason:
                approver = task.approver_ids.filtered(lambda a: a.user_id == request.env.user)
                if approver and approver.status == 'pending':
                    task.sudo().action_cancel(approver, rejection_reason=rejection_reason)
        return request.redirect(f'/task/project/{task_id}/')

