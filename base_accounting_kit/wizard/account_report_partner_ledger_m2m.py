# -*- coding: utf-8 -*-
#############################################################################
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
from odoo import fields, models


class AccountPartnerLedgerM2M(models.TransientModel):
    _inherit = "account.report.partner.ledger"

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Partner List',
        help='Restrict the report to the selected partners only.'
    )

    def _print_report(self, data):
        data = super()._print_report(data)
        # The super returns an ir.actions.report dict when called from button,
        # but we need to inject wizard values into the original data['form'].
        # Therefore, override pre_print_report path by updating context values
        # using the active wizard record and return the original action.
        # Retrieve the action dict and reattach selected partners via context.
        # Note: The report model will read this from the report data when set.
        if isinstance(data, dict) and data.get('data') and data['data'].get('form'):
            form_vals = data['data']['form']
            form_vals.update({'partner_ids': self.partner_ids.ids})
        return data


