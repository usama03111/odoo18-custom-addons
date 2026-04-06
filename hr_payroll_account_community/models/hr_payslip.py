# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrPayslip(models.Model):
    """ Extends the standard 'hr.payslip' model to include additional fields
        for accounting purposes."""
    _inherit = 'hr.payslip'

    date = fields.Date(string='Date Account',
                       help="Keep empty to use the period of the "
                            "validation(Payslip) date.")
    journal_id = fields.Many2one('account.journal',
                                 string='Salary Journal',
                                 required=True,
                                 help="Select Salary Journal",
                                 default=lambda self: self.env[
                                     'account.journal'].search(
                                     [('type', '=', 'general')],
                                     limit=1))
    move_id = fields.Many2one('account.move',
                              string='Accounting Entry',
                              readonly=True, copy=False,
                              help="Accounting entry associated with "
                                   "this record")
    # this field for make a group by department
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True
    )

    note = fields.Html(string="Description")

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
        required=True,
    )

    allowance = fields.Monetary(
        string="Allowance",
        currency_field="currency_id",
        help="Extra allowance amount provided in this contract."
    )
    deduction = fields.Monetary(
        string="Deduction",
        currency_field="currency_id",
        help="Deduction amount applied in this contract."
    )
    bonus = fields.Monetary(
        string="Bonus",
        currency_field="currency_id",
        help="Bonus amount associated with this contract."
    )


    def action_payslip_draft(self):
        """Function for change stage of Payslip"""
        for rec in self:
                reset_by_employee_id = rec.approver_id.reset_by_employee_id
                current_employee = self.env.user.employee_id
                if reset_by_employee_id and reset_by_employee_id != current_employee:
                    raise ValidationError(
                        _("Only %s can reset this payslip to draft. You are not allowed.")
                        % reset_by_employee_id.name)
                    # otherwise, assign current employee as the resetter
        return super(HrPayslip, self).action_payslip_draft()

    @api.model
    def create(self, vals):
        """Create a new payroll slip.This method is called when creating a
            new payroll slip.It checks if 'journal_id' is present in the
            context and, if so, sets the 'journal_id' field in the values."""
        if 'journal_id' in self.env.context:
            vals['journal_id'] = self.env.context.get('journal_id')
        return super(HrPayslip, self).create(vals)

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        """Triggered when the contract associated with the payroll slip is
            changed.This method is called when the 'contract_id' field is
            modified. It invokes the parent class's onchange method and then
            sets the 'journal_id' field based on the 'contract_id's journal or
            the default journal if no contract is selected."""
        super(HrPayslip, self).onchange_contract_id()
        self.journal_id = self.contract_id.journal_id.id or (
                not self.contract_id and
                self.default_get(['journal_id'])['journal_id'])

    def action_payslip_cancel(self):
        """Cancel the payroll slip and associated accounting entries.This
        method cancels the current payroll slip by canceling its associated
        accounting entries (moves). If a move is in the 'posted' state, it is
        first uncanceled, then all moves are unlinked. Finally, the method
        calls the parent class's action_payslip_cancel method."""
        for rec in self:
                reset_by_employee_id = rec.approver_id.reset_by_employee_id
                current_employee = self.env.user.employee_id
                if reset_by_employee_id and reset_by_employee_id != current_employee:
                    raise ValidationError(
                        _("Only %s can reset this payslip to Cancel. You are not allowed.")
                        % reset_by_employee_id.name)
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        return super(HrPayslip, self).action_payslip_cancel()


    def action_payslip_done(self):
        """Finalize and post the payroll slip, creating accounting entries.This
         method is called when marking a payroll slip as done. It calculates
         the accounting entries based on the salary details, creates a move
         (journal entry),and posts it. If necessary, adjustment entries are
         added to balance the debit and credit amounts."""
        res = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            name = _('Payslip of %s') % slip.employee_id.name
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': slip.date or slip.date_to,
            }
            for line in slip.details_by_salary_rule_category_ids:
                amount = slip.company_id.currency_id.round(
                    slip.credit_note and -line.total or line.total)
                if slip.company_id.currency_id.is_zero(amount):
                    continue
                debit_account_id = line.salary_rule_id.account_debit_id.id
                credit_account_id = line.salary_rule_id.account_credit_id.id
                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(
                            credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': slip.date or slip.date_to,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2][
                        'credit']
                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': slip.date or slip.date_to,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2][
                        'debit']
            if slip.company_id.currency_id.compare_amounts(
                    credit_sum, debit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly '
                          'configured the Credit Account!') % (
                            slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': slip.date or slip.date_to,
                    'debit': 0.0,
                    'credit':  slip.company_id.currency_id.round(
                        debit_sum - credit_sum),
                })
                line_ids.append(adjust_credit)
            elif slip.company_id.currency_id.compare_amounts(
                    debit_sum, credit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly '
                          'configured the Debit Account!') % (
                            slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': slip.date or slip.date_to,
                    'debit':  slip.company_id.currency_id.round(
                        credit_sum - debit_sum),
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': slip.date or slip.date_to})
            if not move.line_ids:
                raise UserError(
                    _("As you installed the payroll accounting module you have"
                      " to choose Debit and Credit account for at least one "
                      "salary rule in the chosen Salary Structure."))
            move.action_post()
        return res

    @api.constrains('date_from', 'date_to')
    def _check_no_future_months(self):
        for record in self:
            if record.date_from and record.date_to:
                today = date.today()
                # First day of next month
                if today.month == 12:
                    first_day_next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    first_day_next_month = today.replace(month=today.month + 1, day=1)
                # Validation: end date must be before the first day of next month
                if record.date_to >= first_day_next_month:
                    raise ValidationError(_(
                        "You cannot create payslip for upcoming months."
                    ))