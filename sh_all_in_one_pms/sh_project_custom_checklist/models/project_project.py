# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api

class ProjectProject(models.Model):
    _inherit = "project.project"

    @api.depends("custom_checklist_ids")
    def _compute_custom_checklist(self):
        for rec in self:
            total_cnt = self.env["project.custom.checklist.line"].search_count(
                [("project_id", "=", rec.id), ])

            compl_cnt = self.env["project.custom.checklist.line"].search_count(
                [("project_id", "=", rec.id), ("state", "=", "completed")])

            if total_cnt > 0:
                rec.custom_checklist = (100.0 * compl_cnt) / total_cnt
            else:
                rec.custom_checklist = 0

    custom_checklist_ids = fields.One2many("project.custom.checklist.line",
                                           "project_id", "Checklist")
    custom_checklist = fields.Float(" Checklist Completed ",
                                    compute="_compute_custom_checklist", digits=(12,0))

    checklsit_template = fields.Many2many("project.custom.checklist.template",'checklsit_template_rel',
                                          string="Checklist Template")

    @api.onchange('checklsit_template')
    def onchange_checklsit_template(self):
        update_ids = []
        for i in self.checklsit_template:
            for checklist in i._origin.checklist_template_ids:
                new_id = self.env["project.custom.checklist.line"].create({
                    'name': checklist.id,
                    'description': checklist.description,
                    'company_id': checklist.company_id.id,
                    'project_id': self._origin.id,
                })
                update_ids.append(new_id.id)

        self.custom_checklist_ids = [(6, 0, update_ids)]
