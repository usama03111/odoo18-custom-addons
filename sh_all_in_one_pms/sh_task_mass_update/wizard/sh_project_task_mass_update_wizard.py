# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models

class UpdatemassTag(models.TransientModel):
    _name = "sh.project.task.mass.update.wizard"
    _description = "Mass Update Wizard"

    project_task_ids = fields.Many2many('project.task')
    update_assign_to_bool = fields.Boolean(string="Update Assignees",
                                           default=False)
    update_assignees = fields.Many2many('res.users', string="Assignees")
    update_deadline_bool = fields.Boolean(string="Update Deadline",
                                          default=False)
    deadline = fields.Date()
    update_tags_bool = fields.Boolean(string="Update Tags")
    update_tags = fields.Many2many('project.tags', string="Tags")

    update_method_assignees = fields.Selection([
        ("add", "Add"),
        ("replace", "Replace"),
    ],
        default="add")

    update_method_tags = fields.Selection([
        ("add", "Add"),
        ("replace", "Replace"),
    ],
        default="add")

    update_stage_bool = fields.Boolean(string="Update Stage", default=False)
    stage_id = fields.Many2one('project.task.type')

    update_project_bool = fields.Boolean(
        string="Update Project", default=False)
    project_id = fields.Many2one('project.project')

    def update_record(self):
        if self.update_method_assignees == 'add':
            for i in self.update_assignees:
                self.project_task_ids.write({'user_ids': [(4, i.id)]})

        if self.update_method_assignees == 'replace':
            self.project_task_ids.write(
                {'user_ids': [(6, 0, self.update_assignees.ids)]})

        if self.update_deadline_bool:
            self.project_task_ids.write({'date_deadline': self.deadline})

        if self.update_method_tags == 'add':
            for i in self.update_tags:
                self.project_task_ids.write({'tag_ids': [(4, i.id)]})

        if self.update_method_tags == 'replace':
            self.project_task_ids.write(
                {'tag_ids': [(6, 0, self.update_tags.ids)]})

        if self.update_stage_bool:
            self.project_task_ids.write({'stage_id': self.stage_id.id})

        if self.update_project_bool:
            self.project_task_ids.write({'project_id': self.project_id.id})
