# -*- coding: utf-8 -*-
from odoo import models, fields


class HrExpense(models.Model):
    """
    Inherits the hr.expense model to link expenses with employee travel requests and
    track the number of related journal entries.
    """
    _inherit = 'hr.expense'

    employee_travel_expense_id = fields.Many2one('employee.travel.request', string="Travel Request")

