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

from odoo import fields, models, _ , api
from odoo.exceptions import ValidationError


class HrPayslipRun(models.Model):
    """Extends the standard 'hr.payslip.run' model to include additional fields
    for managing payroll runs.
    Methods:
        compute_total_amount: Compute the total amount of the payroll run."""
    _inherit = 'hr.payslip.run'

    journal_id = fields.Many2one(comodel_name='account.journal',
                                 string='Salary Journal',
                                 required=True, help="Journal associated with "
                                                     "the record",
                                 default=lambda self: self.env[
                                     'account.journal'].search(
                                     [('type', '=', 'general')],
                                     limit=1))

    reference = fields.Char(string='Reference',required=True, copy=False,
                            readonly=True, default=lambda self: _("New"))

    state = fields.Selection(selection_add=[
        ('done', 'Done'),
    ], index=True, copy=False, tracking=True,
        ondelete={'done': 'set default'}
    )

    def done_payslip_run(self):
        for line in self.slip_ids:
            line.action_payslip_done()
        return self.write({'state': 'done'})

    @api.model
    def create(self, values):
        if values.get('reference', _('New')) == _('New'):
            values['reference'] = self.env['ir.sequence'].next_by_code('hr.payslip.run') or _('New')
        res = super(HrPayslipRun, self).create(values)
        return res
