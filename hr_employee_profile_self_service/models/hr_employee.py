from  odoo import fields,models,api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    probation_date = fields.Date(
        string="Probation Start Date",
        help="The date when the employee's probation period begins."
    )