from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def _check_overdue_tasks_and_notify(self):
        today = fields.Date.today()
        overdue_tasks = self.env['project.task'].search([
            ('date_deadline', '<', today),
            ('user_ids', '!=', False),
            ('is_closed', '=', False),  # Skip completed tasks
        ])

        # Load or create email template
        template = self.env.ref('project_task_overdue.email_template_task_overdue', raise_if_not_found=False)

        for task in overdue_tasks:
            if template:
                for user in task.user_ids:
                    if user.email:
                        try:
                            # Use with_context to override template variable
                            template.with_context(email_to=user.email, user_name=user.name).send_mail(task.id, force_send=True)
                            _logger.info(f"Overdue email sent to {user.name} for task '{task.name}' (ID: {task.id})")
                        except Exception as e:
                            _logger.error(f"Error sending overdue email to {user.name} for task '{task.name}': {e}")

        # Send COO summary if there are overdue tasks
        if overdue_tasks:
            self._send_coo_overdue_summary(overdue_tasks)

        return True

    @api.model
    def _send_coo_overdue_summary(self, overdue_tasks):
        """Send a summary of all overdue tasks to all users in the COO group"""
        try:
            # Get all COO users from group
            coo_users = self._get_coo_user()
            if not coo_users:
                _logger.warning("No COO users found in COO group")
                return False

            # Load COO email template
            coo_template = self.env.ref(
                'project_task_overdue.email_template_coo_overdue_summary',
                raise_if_not_found=False
            )
            if not coo_template:
                _logger.error("COO email template not found")
                return False

            # Prepare overdue tasks summary
            today = fields.Date.today()
            overdue_items = []
            for task in overdue_tasks:
                project_name = task.project_id.name if task.project_id else 'No Project'
                assigned_names = ", ".join(task.user_ids.mapped('name')) if task.user_ids else 'Unassigned'
                deadline_value = task.date_deadline
                if hasattr(deadline_value, 'date'):
                    deadline_date = deadline_value.date()
                else:
                    deadline_date = deadline_value
                deadline_str = deadline_value.strftime('%d-%m-%Y') if deadline_value else 'No Deadline'
                days_overdue = (today - deadline_date).days if deadline_date else 0
                overdue_items.append({
                    'name': task.name or 'No Name',
                    'project_name': project_name,
                    'assigned_names': assigned_names,
                    'deadline_str': deadline_str,
                    'days_overdue': days_overdue,
                })

            # Send email to each COO user
            for coo_user in coo_users:
                if not coo_user.email:
                    _logger.warning(f"COO user {coo_user.name} has no email")
                    continue

                context = {
                    'coo_name': coo_user.name,
                    'overdue_items': overdue_items,
                    'total_overdue_count': len(overdue_items),
                    'email_to': coo_user.email,
                }

                # coo_template.with_context(context).send_mail(
                #     res_id=False, force_send=True) # don't attach to chatter
                coo_template.with_context(context).send_mail(overdue_tasks[0].id, force_send=True)
                _logger.info(f"COO overdue summary sent to {coo_user.name} ({coo_user.email}) "
                             f"with {len(overdue_items)} overdue tasks")

            return True

        except Exception as e:
            _logger.error(f"Error sending COO overdue summary: {e}")
            return False

    @api.model
    def _get_coo_user(self):
        coo_group = self.env.ref('project_task_overdue.group_coo_overdue_mail', raise_if_not_found=False)
        if coo_group:
            coo_users = self.env['res.users'].search([('groups_id', 'in', coo_group.id)])
            return coo_users  # returns recordset (could be 1 or many)
        return False
