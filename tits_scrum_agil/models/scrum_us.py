from odoo import models, fields, api, _
import re


class ScrumUserStories(models.Model):
    _name = "project.scrum.us"
    _description = "Project Scrum User Stories"

    name = fields.Char(string='User Story', required=True)
    color = fields.Integer('Color Index')
    description = fields.Html(string='Description')
    description_short = fields.Text(compute='_conv_html2text', store=True)
    actor_ids = fields.Many2many(comodel_name='project.scrum.actors', string='Actor')
    project_id = fields.Many2one(comodel_name='project.project', string='Project', ondelete='set null', track_visibility='onchange')
    sprint_id = fields.Many2one(comodel_name='project.scrum.sprint', string='Sprint')
    task_ids = fields.One2many(comodel_name='project.task', inverse_name='us_id')
    task_count = fields.Integer(compute='_task_count', store=True)
    test_ids = fields.One2many(comodel_name='project.scrum.test', inverse_name='user_story_id_test')
    test_count = fields.Integer(compute='_test_count', store=True)
    sequence = fields.Integer('Sequence')
    # company_id = fields.Many2one(related='project_id.analytic_account_id.company_id')

    def _conv_html2text(self):
        # method that return a short text from description of user story
        for d in self:
            d.description_short = re.sub('<.*>', ' ', d.description or '')
            if len(d.description_short) >= 150:
                d.description_short = d.description_short[:149]

    def _task_count(self):
        # method that calculate how many tasks exist
        for p in self:
            p.task_count = len(p.task_ids)

    def _test_count(self):
        # method that calculate how many test cases exist
        for p in self:
            p.test_count = len(p.test_ids)
