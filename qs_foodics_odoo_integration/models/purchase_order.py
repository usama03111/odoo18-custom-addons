# -*- coding: utf-8 -*-
from odoo import fields, models, _
from datetime import datetime, date
from dateutil import parser
from odoo.tools import float_is_zero
import json


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    foodic_order_id = fields.Char()

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
                'foodics_branch_id': order.get('branch').get('id'),
                'name': order.get('branch').get('name'),
                'code': order.get('branch').get('reference'),
                'plan_id': self.env['account.analytic.plan'].sudo().search([('name', '=', 'CTC')], limit=1).id,
                'company_id': self.env.company.id,
                'currency_id': self.env.company.currency_id.id,
            }
            
            analytic_account_id = self.env['account.analytic.account'].sudo().search([('foodics_branch_id', '=', order.get('branch').get('id'))], limit=1)
            if analytic_account_id:
                if analytic_account_id.name != order.get('branch').get('name') or analytic_account_id.code != order.get('branch').get('reference'):
                    self.env['account.analytic.account'].update(vals)
            else:
                analytic_account_id.create(vals)
            if i % 100 == 0:
                self.env.cr.commit()
        self.env.cr.commit()

    # this method will accept jsonified response once called in the connector module
    def set_orders_to_odoo(self, orders):
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        ProductProduct = self.env['product.template']
        ResPartner = self.env['res.partner']
        AnalyticAccount = self.env['account.analytic.account']
        # iterate through the list of data dictionary/object of json response
        for rec in orders.get('data'):
            lines = []
            # each list item/rec is a dictionary
            order = PurchaseOrder.search([('foodic_order_id', '=', rec.get('id'))])            

            order_date = datetime.strptime(rec.get('created_at'), '%Y-%m-%d %H:%M:%S')
            foodics_response_branch_id = rec.get('branch').get('id')
            analytic_account_id_branch_id = AnalyticAccount.sudo().search([('foodics_branch_id', '=', foodics_response_branch_id),], limit=1).id

            # iterate through each purchase order 
            for item in rec.get('items'):
                prdt = self.env['product.product'].search([('name', '=', item.get('name')), ('active', 'in', [True, False])],limit=1)
                if not prdt:
                    ProductProduct.set_products_to_odoo({'data': [item]})
                    prdt = self.env['product.product'].search([('name', '=', item.get('name')), ('active', 'in', [True, False])],limit=1)

                vals = {'name': prdt.name,
                'product_id': prdt.id,
                'price_unit': (item.get('pivot').get('cost') / item.get('pivot').get('quantity')),
                'product_qty': item.get('pivot').get('quantity'),
                'create_date': order_date,
                'write_date': order_date,
                # 'product_uom': prdt.uom_po_id,
                'taxes_id': ([(4, (self.env.company.account_purchase_tax_id.id))]) if (self.env.company.account_purchase_tax_id) else [], # user must configure a default purchase tax in settings for each used company
                'analytic_distribution': {str(analytic_account_id_branch_id): 100.0},
                }
                po_line = False
                if order:
                    po_line = PurchaseOrderLine.search([('order_id', '=', order.id), ('product_id', '=', prdt.id)])
                    if po_line:
                        lines.append((1, po_line.id, vals)) # po_line must be one record otherwise singleton
                
                if not po_line:
                    lines.append((0, 0, vals))

            supplier = False
            if rec.get('supplier'):
                supplier = ResPartner.search([('foodic_partner_id', '=', rec.get('supplier').get('id')), ('active', 'in', [True, False])], limit=1)
                if not supplier:
                    ResPartner.set_partner_to_odoo({'data': [rec.get('supplier')]})
                    supplier = ResPartner.search([('foodic_partner_id', '=', rec.get('supplier').get('id')), ('active', 'in', [True, False])], limit=1)

            
            vals = {'partner_id': supplier.id,
            'date_order': order_date,
            'order_line': lines,
            'foodic_order_id': rec.get('id')
            }
            if rec.get('reference'):
                vals['name'] = rec.get('reference')

            if not order:
                order = PurchaseOrder.create(vals)
                order.create_date = order_date

            else:
                order.update(vals)
                order.create_date = order_date


            if (int(rec.get('status')) == 3) or (int(rec.get('status')) == 6): #Approved
                order.button_confirm() # or PurchaseOrder.button_confirm()
                order.date_approve = datetime.strptime(rec.get('updated_at'), '%Y-%m-%d %H:%M:%S')
                

            self._cr.commit()
            
