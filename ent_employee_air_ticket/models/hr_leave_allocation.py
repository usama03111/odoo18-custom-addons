from odoo import fields, models

class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    is_air_ticket = fields.Boolean(string="Is Air Ticket", default=False)
