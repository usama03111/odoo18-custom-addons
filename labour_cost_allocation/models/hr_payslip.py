from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    labour_cost_analytic_line_ids = fields.One2many('account.analytic.line', 'payslip_id', string='Labour Cost Analytic Lines')

    # override action_payslip_done to create labor cost analytic entry
    def action_payslip_done(self):
        res = super().action_payslip_done()
        for payslip in self:
            payslip._create_labour_cost_analytic_entry()
        return res

    def _create_labour_cost_analytic_entry(self):
        self.ensure_one()
        AnalyticLine = self.env['account.analytic.line']
        if not self.project_id.account_id:
            raise UserError(_("The selected project '%s' does not have an analytic account linked.") % self.project_id.name)
        analytic_account = self.project_id.account_id
        general_account = False
        if self.struct_id and self.struct_id.journal_id:
            general_account = self.struct_id.journal_id.default_account_id

        if not general_account:
            raise UserError(_("No default expense account found for payroll journal."))

        #Create Line
        vals = {
            'name': _("Labour Cost – %s – %s") % (self.employee_id.name, self.date_to.strftime('%B %Y')),
            'account_id': analytic_account.id ,
            'amount': -self.net_wage,
            'date': self.date_to,
            'general_account_id': general_account.id ,
            'ref': self.number,
            'payslip_id': self.id,
        }
        AnalyticLine.create(vals)

    # Remove analytic entry during the draft
    def action_payslip_draft(self):
        self._remove_labour_cost_analytic_entry()
        return super(HrPayslip, self).action_payslip_draft()

    def _remove_labour_cost_analytic_entry(self):
        for payslip in self:
            payslip.labour_cost_analytic_line_ids.unlink()

