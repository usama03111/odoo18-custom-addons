# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta
from dateutil import parser
from odoo.tools import float_is_zero
import logging
_logger = logging.getLogger(__name__)

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    foodic_payment_id = fields.Char()


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def check(self):
        print("WWWWWWWWW")
        print("WWWWWWWWW")
        """Check the order:
        if the order is not paid: continue payment,
        if the order is paid print ticket.
        """
        self.ensure_one()

        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        currency = order.currency_id

        init_data = self.read()[0]
        if not float_is_zero(init_data['amount'], precision_rounding=currency.rounding):
            order.add_payment({
                'pos_order_id': order.id,
                'amount': order._get_rounded_amount(init_data['amount']),
                'name': init_data['payment_name'],
                'payment_method_id': init_data['payment_method_id'][0],
                'foodic_payment_id': self.env.context.get('foodic_payment_id', False)
            })

        if order._is_pos_order_paid():
            order.action_pos_order_paid()
            order._create_order_picking()
            return {'type': 'ir.actions.act_window_close'}


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_void = fields.Boolean(default=False)
    is_returned = fields.Boolean(default=False)
    foodic_discount = fields.Float('Discount')

class PosOrder(models.Model):
    _inherit = 'pos.order'

    foodic_order_id = fields.Char('Foodic product Id')
    foodic_order_ref = fields.Char('Foodic Order Ref', readonly=True)
    cashier = fields.Char(readonly=True)
    count = fields.Integer(default=0)


    def set_orders_to_odoo(self, res, timestamp):
        try:
            PosConfig = self.env['pos.config']
            ResPartner = self.env['res.partner']
            PosOrder = self.env['pos.order']
            PosSession = self.env['pos.session']
            ProductProduct = self.env['product.template']
            PosOrderLine = self.env['pos.order.line']
            PosPaymentmethod = self.env['pos.payment.method']
            AccountTax = self.env['account.tax']
            if res:
                for order in res.get('data'):
                    print("========================")
                    print(order.get('closed_at'))
                    print("========================")
                    date_order = order.get('business_date')
                    if datetime.strptime(date_order, '%Y-%m-%d') > datetime.strptime(timestamp, '%Y-%m-%d') - timedelta(days=1):
                        continue
    
                    customer = ''
                    branch = PosConfig.search([('foodic_branch_id', '=', order.get('branch').get('id'))], limit=1)
                    if not branch:
                        PosConfig.set_branches_to_odoo({'data': [order.get('branch')]})
                        branch = PosConfig.search([('foodic_branch_id', '=', order.get('branch').get('id'))], limit=1)
                    if order.get('customer'):
                        customer = ResPartner.search([('foodic_partner_id', '=', order.get('customer').get('id'))]).id
                        if not customer:
                            ResPartner.set_partner_to_odoo({'data': [order.get('customer')]})
                            customer = ResPartner.search([('foodic_partner_id', '=', order.get('customer').get('id'))]).id
                    else:
                        customer = False
    
                    pos_order = PosOrder.search([('foodic_order_id', '=', order.get('id'))])
                    session = PosSession.search([('config_id', '=', branch.id), ('state', 'not in', ['closed', 'closing_control'])])
                    if not session:
                        session = session.create({'config_id': branch.id, 'user_id': self.env.uid})
    
                    pos_order_line = []
                    amount_total = 0
                    amount_paid = 0
                    total_tax = 0
                    contain_void_product = True
                    for foodic_prdt in order.get('products'):
                        if foodic_prdt.get('product'):
                            print("Main")
                            print(foodic_prdt.get('product').get('id'))
                            print(foodic_prdt.get('product'))
                            if foodic_prdt.get('status') == 5:
                                continue
                            else:
                                print("ELSE")
                                print(foodic_prdt.get('product').get('id'))
                                print(foodic_prdt.get('status'))
                                if foodic_prdt.get('options'):
                                    for options in foodic_prdt.get('options'):
                                        if options.get('modifier_option'):
                                            prdt = ProductProduct.search([('foodics_item_id', '=', options.get('modifier_option').get('id')), ('active', 'in', [True, False])], limit=1)
                                            if not prdt:
                                                ProductProduct.with_context({'is_modifier': True}).set_products_to_odoo({'data': [options.get('modifier_option')]})
                                                prdt = ProductProduct.search([('foodics_item_id', '=', options.get('modifier_option').get('id')), ('active', 'in', [True, False])], limit=1)
                                            pos_order_line.append((0, 0, {'name': prdt.name,
                                                'full_product_name': prdt.name,
                                                'product_id': prdt.id,
                                                'qty': options.get('quantity'),
                                                'price_subtotal': options.get('total_exclusice_total_price'),
                                                'price_subtotal_incl': 0,
                                                'price_unit': options.get('unit_price')}))
        
                                prdt = ProductProduct.search([('foodics_item_id', '=', foodic_prdt.get('product').get('id')), ('active', 'in', [True, False])],limit=1)
                                if not prdt:
                                    ProductProduct.set_products_to_odoo({'data': [foodic_prdt.get('product')]})
                                    prdt = ProductProduct.search([('foodics_item_id', '=', foodic_prdt.get('product').get('id')), ('active', 'in', [True, False])], limit=1)
        
                                tax_ids = []
                                amount_tax = 0
                                for tax in foodic_prdt.get('taxes'):
                                    amount = tax.get('pivot').get('amount')
                                    foodic_tax = AccountTax.search([('name', '=', 'VAT {}%'.format(tax.get('rate'))), ('amount', '=', tax.get('rate')), ('amount_type', '=', 'percent')]) 
                                    if not foodic_tax:
                                        foodic_tax = AccountTax.create({'name': "VAT {}%".format(tax.get('rate')), 'amount': tax.get('rate'), 'amount_type': 'percent', 'country_id':192})
                                    tax_ids.append(foodic_tax.id)
                                    amount_tax = amount_tax + amount
        
                                is_returned = False
                                total_price = foodic_prdt.get('total_price')
                                if foodic_prdt.get('status') == 6:
                                    is_returned = True
                                    total_price = -foodic_prdt.get('total_price')
        
                                is_void = True
                                foodic_discount =  foodic_prdt.get('discount_amount')
        
                                price_subtotal = foodic_prdt.get('tax_exclusive_total_price')
                                if foodic_prdt.get('status') != 5:
                                    # contain_void_product = False
                                    total_tax = total_tax + amount_tax
                                    # amount_paid = amount_paid + foodic_prdt.get('total_price')
                                    amount_total = amount_total + total_price
                                    is_void = False
        
                                    if total_price == 0:
                                        price_subtotal = foodic_prdt.get('tax_exclusive_unit_price') * foodic_prdt.get('quantity')
        
                                vals = (0 ,0 ,{'name': prdt.name,
                                    'full_product_name': prdt.name,
                                    'qty': foodic_prdt.get('quantity'),
                                    'product_id': prdt.id,
                                    'price_unit': foodic_prdt.get('tax_exclusive_unit_price'),
                                    'price_subtotal': price_subtotal,
                                    'price_subtotal_incl': total_price,
                                    'tax_ids': [(6, 0, tax_ids)] if tax_ids else [],
                                    'is_void': is_void,
                                    'is_returned': is_returned,
                                    'foodic_discount': foodic_discount
                                    })
                                pos_order_line.append(vals)
    
                    if not pos_order_line:
                        continue
    
                    for charge in order.get('charges'):
                        amount_total += charge.get('amount')
    
                    date_order = order.get('business_date')
                    if date_order:
                        date_order = datetime.strptime(date_order, '%Y-%m-%d')
                    if order.get('discount_amount'):
                        amount_total -= order.get('discount_amount')
                    if not pos_order:
                        cashier = ''
                        if order.get('creator'):
                            cashier = order.get('creator').get('name')
    
                        pos_order = PosOrder.create({
                            'foodic_order_ref': order.get('reference'),
                            'cashier': cashier,
                            'foodic_order_id': order.get('id'),
                            'session_id': session.id,
                            'partner_id': customer,
                            'date_order': date_order,
                            'lines': pos_order_line,
                            'amount_total': amount_total,
                            'amount_tax': total_tax,
                            'amount_return': 0,
                            'amount_paid': 0,
                            })
                    else:
                        pos_order.date_order = date_order
                    context_make_payment = {"active_id": pos_order.id}
    
                    if amount_total == 0 and pos_order.state != 'paid':
                        payment_date = date_order # date.today().strftime('%Y-%m-%d')
                        pos_payment = pos_order.config_id.payment_method_ids[0]
                        make_payment = self.env['pos.make.payment'].with_context(context_make_payment).create({
                            'payment_date': payment_date,
                            'payment_method_id': pos_payment.id,
                            'config_id': branch.id,
                            'amount': amount_total,
                        })
                        make_payment.check()
                        amount_paid = amount_total
                        continue
    
                    payments = pos_order.payment_ids.filtered(lambda payment: payment.foodic_payment_id != False)
                    for payment in order.get('payments'):
                        if payment.get('id') in payments.mapped('foodic_payment_id'):
                            continue
    
                        payment_date = payment.get('business_date')
                        if payment_date:
                            payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
                        else:
                            payment_date = date_order # date.today().strftime('%Y-%m-%d')
    
                        pos_payment = PosPaymentmethod.sudo().search([('foodic_payment_method_id', '=', payment.get('payment_method').get('id'))], limit=1)
                        if not pos_payment:
                            PosPaymentmethod.set_payment_methods_to_odoo({'data': [payment.get('payment_method')]})
                            pos_payment = PosPaymentmethod.sudo().search([('foodic_payment_method_id', '=', payment.get('payment_method').get('id'))])
    
                        make_payment = self.env['pos.make.payment'].with_context(context_make_payment).create({
                            'payment_date': payment_date,
                            'payment_method_id': pos_payment.id,
                            'config_id': branch.id,
                            'amount': payment.get('amount'),
                        })
                        amount_paid = amount_paid + payment.get('amount')
                        ctx = make_payment.env.context.copy()
                        ctx.update({'foodic_payment_id': payment.get('id')})
                        make_payment.with_context(ctx).check()
                        self._cr.commit()
                        # update payment date because odoo internally insert the current datetime
                        payment_stored_data = self.env['pos.payment'].sudo().search([('foodic_payment_id', '=', payment.get('id'))], limit=1)
                        payment_stored_data.update({'payment_date': date_order})
                    pos_order.amount_paid = amount_paid
                    self._cr.commit()
            return False
        except Exception as e:
            _logger.error(e)
            raise UserError((f"Something went wrong while creating/updating POS orders in Odoo!\nPlease try again later\nHere's the available technical details of what happened:\n{e}"))
