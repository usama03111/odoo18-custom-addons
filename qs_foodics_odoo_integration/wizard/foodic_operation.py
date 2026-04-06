from odoo import models, fields, _
import asyncio
import threading
import datetime
from odoo.exceptions import UserError

class FoodicOperation(models.TransientModel):
    _name = "foodic.operation"
    _description = 'foodic operations'

    foodic_instance_id = fields.Many2one('foodics.connector')

    from_date = fields.Date(string='Starting Date', help="Any request with an entered date in this field means that\n the response would include recorded entries on this date and afterwards, ending with the current date at the moment of request or the ending date (if entered)")
    before_date = fields.Date(string='Ending Date', help="Any request with an entered date in this field means that\n the response would include recorded entries on this date and beforehand, starting with the first ever recorded entry or the starting date (if entered)")
    
    operation = fields.Selection([('sync_branch', 'Import POS Branch'),
                                ('sync_payment_method', 'Import Payment Methods'),
                                ('sync_categories', 'Import Categories'),
                                ('sync_products', 'Import Products'),
                                ('sync_invent_loc', 'Import Inventory Locations'),
                                ('sync_invent_trans', 'Import Inventory Transfers'),
                                ('sync_invent_count', 'Import Inventory Counts'),
                                ('sync_orders', 'Import Orders'),
                                # ('sync_suppliers', 'Import Suppliers'),
                                # ('sync_inventory_items', 'Import Inventory Items'),
                                # ('sync_modifier_products', 'Import Modifier Product'),
                                ('sync_purchase_order', 'Import Purchase Order'),
                                # ('sync_transactions', 'Import Transactions'),
                                ], default="sync_branch", required=True)

    def foodic_execute(self):
        foodic = self.foodic_instance_id
        if self.operation == 'sync_branch':
            foodic.get_branches()
        elif self.operation == 'sync_suppliers':
            foodic.get_suppliers()
        elif self.operation == 'sync_payment_method':
            foodic.get_payment_methods()
        elif self.operation == 'sync_categories':
            foodic.get_categories_methods()
        elif self.operation == 'sync_products':
            asyncio.run(foodic.with_context({'is_modifier': False}).get_products_methods())
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': ("Products have been Successfully imported"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        elif self.operation == 'sync_invent_loc':
            asyncio.run(foodic.get_invent_locations_methods())
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': ("Inventory locations have been Successfully imported"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        elif self.operation == 'sync_invent_trans':
            if self.before_date and self.from_date:
                if self.before_date < self.from_date:
                    raise UserError("The starting date cannot be after the ending date")

            asyncio.run(foodic.get_invent_transactions_methods(self.from_date, self.before_date))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': ("Inventory transactions have been Successfully imported"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        elif self.operation == 'sync_invent_count':
            if self.before_date and self.from_date:
                if self.before_date < self.from_date:
                    raise UserError("The starting date cannot be after the ending date")
                # the backend translate  object 
                # else:
                    # self.from_date = self.from_date - datetime.timedelta(days=1)
                    # self.before_date = self.before_date + datetime.timedelta(days=1)
            asyncio.run(foodic.get_invent_count_methods(self.from_date, self.before_date))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': ("Inventory counts have been Successfully imported"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        elif self.operation == 'sync_orders':
            if self.before_date and self.from_date:
                if self.before_date < self.from_date:
                    raise UserError("The starting date cannot be after the ending date")
                else:
                    self.from_date = self.from_date - datetime.timedelta(days=1)
                    self.before_date = self.before_date + datetime.timedelta(days=1)
            foodic.get_orders_methods(self.from_date, self.before_date)
        elif self.operation == 'sync_inventory_items':
            foodic.get_inventory_items()
        elif self.operation == 'sync_modifier_products':
            foodic.with_context({'is_modifier': True}).get_products_methods()
        elif self.operation == 'sync_purchase_order':
            if self.before_date and self.from_date:
                if self.before_date < self.from_date:
                    raise UserError("The starting date cannot be after the ending date")

            foodic.foodics_import_purchase_orders(self.from_date, self.before_date)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Purchase orders have been Successfully imported."),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        elif self.operation == 'sync_import_warehouse':
            foodic.foodics_import_warehouse()
        elif self.operation == 'sync_transactions':
            foodic.foodics_import_transactions()
            
