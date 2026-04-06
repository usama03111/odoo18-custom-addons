# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    foodic_branch_id = fields.Char('Foodic Branch Id')
    opening_from = fields.Char('Opening From')
    opening_to = fields.Char('Opening To')
    reference = fields.Char('Reference')
    name_localized = fields.Char('Name Localized')
    phone = fields.Char('Phone')
    def set_analytic_plan(self):

        vals = {
            'name': "CTC",
            'default_applicability': "optional",
            'color': 3,
            'company_id': self.env.company.id,
        }
        
        analytic_plan_id = self.env['account.analytic.plan'].sudo().search([('name', '=', 'CTC')], limit=1)
        if analytic_plan_id:
            pass
        else:
            analytic_plan_id.create(vals)
        self.env.cr.commit()
    

    def set_analytic_accounts_to_odoo(self, res):
        self.set_analytic_plan()
        i = 0
        for order in res.get('data'):
            i += 1

            vals = {
                'foodics_branch_id': order.get('id'),
                'name': order.get('name'),
                'code': order.get('reference'),
                'plan_id': self.env['account.analytic.plan'].sudo().search([('name', '=', 'CTC')], limit=1).id,
                'company_id': self.env.company.id,
                'currency_id': self.env.company.currency_id.id,
            }
            
            analytic_account_id = self.env['account.analytic.account'].sudo().search([('foodics_branch_id', '=', order.get('id'))], limit=1)
            if analytic_account_id:
                if analytic_account_id.name != order.get('name') or analytic_account_id.code != order.get('reference'):
                    self.env['account.analytic.account'].update(vals)
            else:
                analytic_account_id.create(vals)
            if i % 100 == 0:
                self.env.cr.commit()
        self.env.cr.commit()
        
    def set_branches_to_odoo(self, res):
        i = 0
        self.set_analytic_accounts_to_odoo(res)
        for branch in res.get('data'):
            i += 1
            vals = {
                'foodic_branch_id': branch.get('id'),
                'name': branch.get('name'),
                'name_localized': branch.get('name_localized'),
                'reference': branch.get('reference'),
                'phone': branch.get('phone'),
                'opening_from': branch.get('opening_from'),
                'opening_to': branch.get('opening_to'),
                'module_pos_restaurant': True,
            }
            branch_id = self.search([('foodic_branch_id', '=', branch.get('id'))], limit=1)
            if branch_id:
                branch_id.update(vals)
            else:
                branch_id.create(vals)
            if i % 100 == 0:
                self.env.cr.commit()
        self.env.cr.commit()
