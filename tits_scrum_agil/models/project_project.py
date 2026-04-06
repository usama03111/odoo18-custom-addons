from odoo import models, fields, api, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sprint_ids = fields.One2many(comodel_name="project.scrum.sprint", inverse_name="project_id", string="Sprints")
    user_story_ids = fields.One2many(comodel_name="project.scrum.us", inverse_name="project_id", string="User Stories")
    meeting_ids = fields.One2many(comodel_name="project.scrum.meeting", inverse_name="project_id", string="Meetings")
    test_case_ids = fields.One2many(comodel_name="project.scrum.test", inverse_name="project_id", string="Test Cases")
    sprint_count = fields.Integer(compute='_sprint_count', string="Sprints")
    user_story_count = fields.Integer(compute='_user_story_count', string="User Stories")
    meeting_count = fields.Integer(compute='_meeting_count', string="Meetings")
    test_case_count = fields.Integer(compute='_test_case_count', string="Test Cases")
    use_scrum = fields.Boolean(store=True, help="True if project use scrum method")
    default_sprintduration = fields.Integer(string='Calendar', required=False, default=14,
                                            help="Default Sprint time for this project, in days")
    manhours = fields.Integer(string='Man Hours', required=False,
                              help="How many hours you expect this project needs before it's finished")

    def _sprint_count(self):
        # method that calculate how many sprints exist
        for p in self:
            p.sprint_count = len(p.sprint_ids)

    def _user_story_count(self):
        # method that calculate how many user stories exist
        for p in self:
            p.user_story_count = len(p.user_story_ids)

    def _meeting_count(self):
        # method that calculate how many meetings exist
        for p in self:
            p.meeting_count = len(p.meeting_ids)

    def _test_case_count(self):
        # method that calculate how many test cases exist
        for p in self:
            p.test_case_count = len(p.test_case_ids)