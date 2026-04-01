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
from odoo import api, models


class ReportPartnerLedgerM2M(models.AbstractModel):
    _inherit = 'report.base_accounting_kit.report_partnerledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        values = super()._get_report_values(docids, data=data)
        form = values.get('data', {}).get('form', {}) if isinstance(values, dict) else {}
        selected_partner_ids = form.get('partner_ids') or []
        if selected_partner_ids:
            # Filter docs and doc_ids to the explicitly selected partners, preserving order
            docs = values.get('docs')
            if docs is not None:
                # docs may be a Python list (since original code uses sorted())
                selected_set = set(selected_partner_ids)
                filtered_docs = [p for p in docs if p.id in selected_set]
                id_to_index = {pid: idx for idx, pid in enumerate(selected_partner_ids)}
                filtered_docs.sort(key=lambda p: id_to_index.get(p.id, 0))
                values['docs'] = filtered_docs
                values['doc_ids'] = [p.id for p in filtered_docs]
        return values


