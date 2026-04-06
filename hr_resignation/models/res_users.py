from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    kb_res_dept_manager = fields.Boolean(string="Resignation: Department Manager")
    kb_res_hr_employee = fields.Boolean(string="Resignation: HR Employee")
    kb_res_hr_manager = fields.Boolean(string="Resignation: HR Manager")
    kb_res_payroll_employee = fields.Boolean(string="Resignation: Payroll Employee")
    kb_res_cfo = fields.Boolean(string="Resignation: CFO")

    @api.constrains(
        'kb_res_dept_manager', 'kb_res_hr_employee', 'kb_res_hr_manager',
        'kb_res_payroll_employee', 'kb_res_cfo'
    )
    def _check_unique_resignation_roles(self):
        """
        Optional (recommended):
        Har role pe sirf 1 user True ho.
        Multiple allow karna ho to yeh constraint hata do.
        """
        roles = [
            ('kb_res_dept_manager', _("Resignation: Department Manager")),
            ('kb_res_hr_employee', _("Resignation: HR Employee")),
            ('kb_res_hr_manager', _("Resignation: HR Manager")),
            ('kb_res_payroll_employee', _("Resignation: Payroll Employee")),
            ('kb_res_cfo', _("Resignation: CFO")),
        ]
        for field_name, label in roles:
            if any(u[field_name] for u in self):
                cnt = self.sudo().search_count([(field_name, '=', True), ('active', '=', True)])
                if cnt > 1:
                    raise ValidationError(_("%s: Only one user can be True at a time.") % label)
