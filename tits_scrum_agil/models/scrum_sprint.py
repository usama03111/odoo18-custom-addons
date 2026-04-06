from odoo import models, fields, api, _
from datetime import date, timedelta


class ScrumSprint(models.Model):
    _name = "project.scrum.sprint"
    _description = "Project Scrum sprint"

    name = fields.Char(string='Sprint Name', required=True)
    meeting_ids = fields.One2many(comodel_name='project.scrum.meeting', inverse_name='sprint_id', string='Daily Scrum')
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned to')
    date_start = fields.Date(string='Starting Date', default=fields.Date.today())
    date_stop = fields.Date(string='Ending Date')
    date_duration = fields.Integer(compute='_compute_hours', string='Duration(in hours)')
    description = fields.Text(string='Description', required=False)
    project_id = fields.Many2one(comodel_name='project.project', string='Project',
                                 track_visibility='onchange',
                                 required=True,
                                 help="If you have [?] in the project name, it means there are no analytic account linked to this project.")
    product_owner_id = fields.Many2one(comodel_name='res.users', string='Product Owner', required=False,
                                       help="The person who is responsible for the product")
    scrum_master_id = fields.Many2one(comodel_name='res.users', string='Scrum Master', required=False,
                                      help="The person who is maintains the processes for the product")
    us_ids = fields.One2many(comodel_name='project.scrum.us', string='User Stories', inverse_name='sprint_id')
    task_ids = fields.One2many(comodel_name='project.task', inverse_name='sprint_id')
    review = fields.Html(string='Sprint Review', default="""
           <h1 style="color:blue"><ul>What was the goal of this sprint?</ul></h1><br/><br/>
           <h1 style="color:blue"><ul>Has the goal been reached?</ul></h1><br/><br/>
       """)
    retrospective = fields.Html(string='Sprint Retrospective', default="""
           <h1 style="color:blue"><ul>What will you start doing in next sprint?</ul></h1><br/><br/>
           <h1 style="color:blue"><ul>What will you stop doing in next sprint?</ul></h1><br/><br/>
           <h1 style="color:blue"><ul>What will you continue doing in next sprint?</ul></h1><br/><br/>
       """)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of tasks.")
    progress = fields.Float(compute="_compute_progress", group_operator="avg", type='float', multi="progress",
                            string='Progress (0-100)', help="Computed as: Time Spent / Total Time.")
    effective_hours = fields.Float(compute="_hours_get", multi="effective_hours", string='Effective hours',
                                   help="Computed using the sum of the task work done.")
    planned_hours = fields.Float(multi="planned_hours", string='Planned Hours',
                                 help='Estimated time to do the task, usually set by the project manager when the task is in draft state.')
    stage_id = fields.Many2one('project.sprint.stage', string="stage")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    task_count = fields.Integer(compute='_task_count', store=True)

    @api.depends('date_start', 'date_stop')
    def _compute_hours(self):
        # compute Duration( in hours)'
        for record in self:
            if record.date_start and record.date_stop:
                record.date_duration = record.time_cal() * 9 if date.today() >= fields.Date.from_string(
                    record.date_stop) else (date.today() - fields.Date.from_string(record.date_start)).days * 9
            else:
                record.date_duration = 0

    def _compute_progress(self):
        # compute progress
        for record in self:
            record.progress = record.effective_hours / record.planned_hours * 100 if record.planned_hours and record.effective_hours and record.planned_hours != 0 else 0

    def _hours_get(self):
        # compute effective_hours
        effective_hours = 0.0
        if self.project_id.allow_timesheets:
            for task in self.task_ids.filtered(lambda x: x.timesheet_ids):
                effective_hours += round(sum(task.timesheet_ids.mapped('unit_amount')), 2)
        self.effective_hours = effective_hours

    def time_cal(self):
        #get time cal
        if self.date_start and self.date_stop:
            if (self.date_stop - self.date_start).days <= 0:
                return 1
            else:
                return (self.date_stop - self.date_start).days + 1

    @api.onchange('date_start')
    def onchange_date_start(self):
        if self.date_start and self.project_id:
            self.date_stop = fields.Date.from_string(self.date_start) + timedelta(
                    days=self.project_id.default_sprintduration)

    def _task_count(self):
        # method that calculate how many tasks exist
        for p in self:
            p.task_count = len(p.task_ids)
