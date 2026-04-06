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
from odoo import api, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        lines = super()._get_payslip_lines(contract_ids, payslip_id)
        if not lines:
            return lines
        payslip = self.env['hr.payslip'].browse(payslip_id)
        allowance = getattr(payslip, 'allowance', 0.0) or 0.0
        bonus = getattr(payslip, 'bonus', 0.0) or 0.0
        deduction = getattr(payslip, 'deduction', 0.0) or 0.0
        
        # Get contract for the payslip
        contract = payslip.contract_id
        if not contract:
            return lines
            
        # Get existing categories
        alw_category = self.env['hr.salary.rule.category'].search([('code', '=', 'ALW')], limit=1)
        ded_category = self.env['hr.salary.rule.category'].search([('code', '=', 'DED')], limit=1)
        
        # Create temporary salary rules for our custom fields
        allowance_rule = self._get_or_create_temp_rule('ALLOWANCE', 'Allowance', alw_category.id if alw_category else False)
        bonus_rule = self._get_or_create_temp_rule('BONUS', 'Bonus', alw_category.id if alw_category else False)
        deduction_rule = self._get_or_create_temp_rule('DEDUCTION', 'Deduction', ded_category.id if ded_category else False)
        
        # Add separate lines for allowance, bonus, and deduction if they have values
        if allowance > 0:
            lines.append({
                'salary_rule_id': allowance_rule.id,
                'contract_id': contract.id,
                'name': 'Allowance',
                'code': 'ALLOWANCE',
                'category_id': alw_category.id if alw_category else False,
                'sequence': 100,  # High sequence to appear after basic rules
                'appears_on_payslip': True,
                'condition_select': 'none',
                'condition_python': '',
                'condition_range': '',
                'condition_range_min': 0.0,
                'condition_range_max': 0.0,
                'amount_select': 'fix',
                'amount_fix': allowance,
                'amount_python_compute': '',
                'amount_percentage': 0.0,
                'amount_percentage_base': '',
                'register_id': False,
                'amount': allowance,
                'employee_id': contract.employee_id.id,
                'quantity': 1.0,
                'rate': 100.0,
            })
            
        if bonus > 0:
            lines.append({
                'salary_rule_id': bonus_rule.id,
                'contract_id': contract.id,
                'name': 'Bonus',
                'code': 'BONUS',
                'category_id': alw_category.id if alw_category else False,
                'sequence': 101,  # High sequence to appear after basic rules
                'appears_on_payslip': True,
                'condition_select': 'none',
                'condition_python': '',
                'condition_range': '',
                'condition_range_min': 0.0,
                'condition_range_max': 0.0,
                'amount_select': 'fix',
                'amount_fix': bonus,
                'amount_python_compute': '',
                'amount_percentage': 0.0,
                'amount_percentage_base': '',
                'register_id': False,
                'amount': bonus,
                'employee_id': contract.employee_id.id,
                'quantity': 1.0,
                'rate': 100.0,
            })
            
        if deduction > 0:
            lines.append({
                'salary_rule_id': deduction_rule.id,
                'contract_id': contract.id,
                'name': 'Deduction',
                'code': 'DEDUCTION',
                'category_id': ded_category.id if ded_category else False,
                'sequence': 102,  # High sequence to appear after basic rules
                'appears_on_payslip': True,
                'condition_select': 'none',
                'condition_python': '',
                'condition_range': '',
                'condition_range_min': 0.0,
                'condition_range_max': 0.0,
                'amount_select': 'fix',
                'amount_fix': deduction,
                'amount_python_compute': '',
                'amount_percentage': 0.0,
                'amount_percentage_base': '',
                'register_id': False,
                'amount': deduction,
                'employee_id': contract.employee_id.id,
                'quantity': 1.0,
                'rate': 100.0,
            })
        
        # Now adjust GROSS and NET lines
        for line in lines:
            code = line.get('code')
            if not code:
                continue

            # Add allowance + bonus to GROSS
            if code == 'GROSS':
                line['amount'] = (line.get('amount', 0.0) or 0.0) + allowance + bonus

            # Deduction should be applied AFTER gross modifications
            if code == 'NET':
                gross_line = next((l for l in lines if l.get('code') == 'GROSS'), None)
                unpaid_line = next((l for l in lines if l.get('code') == 'UL'), None)
                gross_amount = gross_line.get('amount', 0.0) if gross_line else 0.0
                unpaid_amount = unpaid_line.get('amount', 0.0) if unpaid_line else 0.0
                line['amount'] = gross_amount - deduction - unpaid_amount

        return lines

    def _get_or_create_temp_rule(self, code, name, category_id):
        """Create or get temporary salary rule for custom fields"""
        # First try to find existing rule
        existing_rule = self.env['hr.salary.rule'].search([('code', '=', code)], limit=1)
        if existing_rule:
            return existing_rule
            
        # Create a temporary rule if not found
        return self.env['hr.salary.rule'].create({
            'name': name,
            'code': code,
            'sequence': 200,  # High sequence
            'category_id': category_id,
            'active': True,
            'appears_on_payslip': True,
            'condition_select': 'none',
            'condition_python': '',
            'condition_range': '',
            'condition_range_min': 0.0,
            'condition_range_max': 0.0,
            'amount_select': 'fix',
            'amount_fix': 0.0,
            'amount_python_compute': '',
            'amount_percentage': 0.0,
            'amount_percentage_base': '',
            'register_id': False,
        })
