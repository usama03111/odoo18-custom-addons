from odoo import models, fields,api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_attachment = fields.Binary(string="Qid Attachment")
    employee_attachment_name = fields.Char(string="Attachment Name")
    emp_sequence_number = fields.Char(string="Employee Sequence Number")

    joining_date = fields.Date(string="Joining Date")
    expiry_date = fields.Date(string=" Qid Expiry Date")

    # --------------------
    # Salary Certificate
    # --------------------
    salary_cert_addressee = fields.Char(
        string="Salary Certificate Addressee",
        help="The addressee / 'To' field printed on the Salary Certificate.",
    )
 