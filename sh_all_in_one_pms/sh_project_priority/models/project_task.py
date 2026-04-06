# Part of Softhealer Technologies.
from odoo import models, fields,api

class ProjectTask(models.Model):
    _inherit = "project.task"

    sh_priority = fields.Selection([('0', 'Low'), (
        '1', 'Medium'), ('2', 'High'), ('3', 'Very High')],string="Priority")

    enable_project_priority = fields.Boolean(
        related="company_id.enable_project_priority")

    @api.onchange('project_id')
    def _onchange_priority(self):
        if self.project_id.default_added_to_task:
            self.sh_priority = self.project_id.sh_priority
        else:
            self.write({'sh_priority': '0'})
