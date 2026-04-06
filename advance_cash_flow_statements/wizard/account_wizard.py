# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abbas P (odoo@cybrosys.com)
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
################################################################################
import json
from datetime import datetime
from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import json_default
import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountWizard(models.TransientModel):
    _name = "account.wizard"
    _description = 'Account Wizard'

    name = fields.Char(default="Invoice", help='Name of Invoice ')
    date_from = fields.Date(string="Start Date", required=True,
                            help='Date at which report need to be start')
    date_to = fields.Date(string="End Date", default=fields.Date.today,
                          required=True,
                          help='Date at which report need to be end')
    today = fields.Date("Report Date", default=fields.Date.today,
                        help='Date at which report is generated')
    levels = fields.Selection([('summary', 'Summary'),
                               ('consolidated', 'Consolidated'),
                               ('detailed', 'Detailed'),
                               ('very', 'Very Detailed')],
                              string='Levels', required=True, default='summary',
                              help='Different levels for cash flow statements\n'
                                   'Summary: Month wise report.\n'
                                   'Consolidated: Based on account types.\n'
                                   'Detailed: Based on accounts.\n'
                                   'Very Detailed: Accounts with their move lines')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True,
                                   default='posted', help='Type of entries')

    def generate_pdf_report(self):
        """ Generate the pdf reports and return values to template"""
        self.ensure_one()
        logged_users = self.env['res.company']._company_default_get(
            'account.account')
        if self.date_from:
            if self.date_from > self.date_to:
                raise UserError(_("Start date should be less than end date"))
        data = {
            'ids': self.ids,
            'model': self._name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'levels': self.levels,
            'target_move': self.target_move,
            'today': self.today,
            'logged_users': logged_users.name,
        }
        return self.env.ref(
            'advance_cash_flow_statements.pdf_report_action').report_action(
            self,
            data=data)
