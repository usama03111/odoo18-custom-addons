from odoo import fields, models, _
from datetime import datetime
import re
from odoo.exceptions import UserError
import logging



_logger = logging.getLogger(__name__)

class InventCounts(models.Model):
    _inherit = 'stock.quant'

    foodics_count_id = fields.Char('Foodics Count Object ID', index="trigram")
    foodics_count_reference = fields.Char('Foodics Count Object Reference', index="trigram")
    foodics_count_date = fields.Date('Foodics Count Object Date')
    '''
        def set_count_to_odoo(self, res):
            _logger.info('called the transfers method')
            InventoryLocation = self.env['stock.location']
            Product = self.env['product.template']

            try:
                for count in (res.get('data')):
                    print(count['id'])
                    # multiple stock moves will have the same inventory count id which will serve to make those group of distinct count object
                    
                    inventory_location_stored_data = InventoryLocation.sudo().search([('foodics_branch_id', '=', count.get('branch').get('id'))], limit=1)
                    if not inventory_location_stored_data:
                        vals = {
                        'foodics_branch_id': count.get('branch').get('id'),
                        'name': count.get('branch').get('name'),
                        'usage': "internal"
                        # check with implementors if they need other options to be checked such as replenishment
                        }

                        InventoryLocation.sudo().create(vals)
                        self.env.cr.commit()

                    for product in count.get('items'):
                        product_stored_data = Product.sudo().search([('foodics_item_id', '=', product['id'])], limit=1)
                        if not product_stored_data:
                        
                            vals = {
                            'categ_id': 2,
                            'detailed_type': 'product',
                            'name': product['name'] if product['name'] else False,
                            'purchase_line_warn': 'no-message',
                            'sale_line_warn': 'no-message',
                            'uom_id': 1, 
                            'uom_po_id': 1,

                            'foodics_item_id': product['id'],
                            'default_code': False if product['sku'] is None else product['sku'],
                            'barcode': product['barcode'] if product['barcode'] else False,
                            'name_localized': product['name_localized'] if product['name_localized'] else False,
                            'list_price': product['cost'],
                            'standard_price': product['cost'],
                            'available_in_pos': False,
                            'sale_ok': True,
                            'active': True,
                        }
                            if product['deleted_at']:
                                vals['active'] = False

                            created_product = self.env['product.template'].sudo().create(vals)
                            self.env.cr.commit()
                        
                        count_product_stored_data = self.search([('foodics_count_reference', '=', count['id']), ('product_id', '=', product_stored_data.product_variant_id.id)])
                        if count_product_stored_data:
                            continue
                        else:
                            vals = {
                                'product_id': created_product.product_variant_id.id,
                                'location_id': inventory_location_stored_data.id,
                                'inventory_quantity': product.pivot.quantity,
                                'foodics_count_reference': count.id
                            }

                            self.sudo().create(vals)
                            self.env.cr.commit()
                            self.sudo().action_apply_inventory()
            except Exception as e:
                _logger.error(e)
                self.env.cr.rollback()
    '''


    def set_count_to_odoo(self, res):
        _logger.info('called the counts method')
        Product = self.env['product.template']
        InventoryLocation = self.env['stock.location']
        StockMoveLine = self.env['stock.move.line']

        try:
            for count in (res.get('data')):
                print(count['id'])
                # multiple stock moves will have the same inventory count id which will serve to make those group of distinct count object
                
                inventory_location_stored_data = InventoryLocation.sudo().search([('foodics_branch_id', '=', count.get('branch').get('id'))], limit=1)
                if not inventory_location_stored_data:
                    vals = {
                    'foodics_branch_id': count.get('branch').get('id'),
                    'name': count.get('branch').get('name'),
                    'usage': "internal"
                    # check with implementors if they need other options to be checked such as replenishment
                    }

                    inventory_location_stored_data = InventoryLocation.sudo().create(vals)
                    self.env.cr.commit()
                stock_record_ids = []
                for product in count.get('items'):
                    product_stored_data = Product.sudo().search([('foodics_item_id', '=', product['id'])], limit=1)
                    if not product_stored_data:
                    
                        vals = {
                        'categ_id': 2,
                        'detailed_type': 'product',
                        'name': product['name'] if product['name'] else False,
                        'purchase_line_warn': 'no-message',
                        'sale_line_warn': 'no-message',
                        'uom_id': 1, 
                        'uom_po_id': 1,

                        'foodics_item_id': product['id'],
                        'default_code': False if product['sku'] is None else product['sku'],
                        'barcode': product['barcode'] if product['barcode'] else False,
                        'name_localized': product['name_localized'] if product['name_localized'] else False,
                        'list_price': product['cost'],
                        'standard_price': product['cost'],
                        'available_in_pos': False,
                        'sale_ok': True,
                        'active': True,
                    }
                        if product['deleted_at']:
                            vals['active'] = False

                        product_stored_data = self.env['product.template'].sudo().create(vals)
                        self.env.cr.commit()
                    # count_product_stored_data = StockMoveLine.search([('reference', '>', count['reference']), ('product_id', '=', product_stored_data.product_variant_id.id)], order='reference DESC')
                    # search for any record for this product greater than the business day of this count as we won't allow creation of this count
                    # count_product_stored_data = self.search([('foodics_count_date', '>', count['business_date']), ('product_id', '=', product_stored_data.product_variant_id.id)], order='foodics_count_reference DESC', limit=1)
                    
                    count_product_stored_data = self.search([('foodics_count_reference', '=like', "IC-%"), ('product_id', '=', product_stored_data.product_variant_id.id)], order='foodics_count_reference DESC', limit=1)
                    '''
                    because one date can have multiple adjustment objects which reflect that multiple operations have been performed in one day, no provided attribute has sequential nature other than 'foodics_count_reference'
                    one should check if the date of re
                    txt = 'IC-001312, 2024-01-01, 9afcf1d7-19d8-48fa-a30e-d4ed03ed5f4f'
                    if re.search('(\d{4})-(\d{2})-(\d{2})', txt):
                    '''
                    # if not count_product_stored_data:
                    if count_product_stored_data:
                        # continue
                        if count_product_stored_data.foodics_count_reference >= count['reference']: # lexicographic order
                            continue
                        else:
                            # product_stock_quant_stored_data = self.search([('location_id', '=', inventory_location_stored_data.id), ('product_id', '=', product_stored_data.product_variant_id.id)])
                            # should one add this check or create new records directly
                            # if product_stock_quant_stored_data:
                            #     vals = {
                            #         'inventory_quantity': product.pivot.quantity,
                            #         'foodics_count_reference': count.id
                            #     }                        
                            #     stock_adjust_record = self.sudo().update(vals)
                            #     self.env.cr.commit()
                            #     stock_record_ids.append(stock_adjust_record)
                            # else:
                            _logger.info(product)
                            vals = {
                                'product_id': product_stored_data.product_variant_id.id,
                                'location_id': inventory_location_stored_data.id,
                                'inventory_quantity': product['pivot']['quantity'], # shows error if member access operator is used
                                'foodics_count_id': count['id'],
                                'foodics_count_reference': count['reference'],
                                'foodics_count_date': count['business_date'] # shows error if member access operator is used
                            }

                            stock_adjust_record = self.sudo().create(vals)
                            self.env.cr.commit()
                            stock_adjust_record.action_apply_inventory()
                            # stock_record_ids.append(stock_adjust_record.id)
                            self.env.cr.commit()
                    else:
                        # create the first ever inventory count from foodics
                        _logger.info(product)
                        vals = {
                            'product_id': product_stored_data.product_variant_id.id,
                            'location_id': inventory_location_stored_data.id,
                            'inventory_quantity': product['pivot']['quantity'], # shows error if member access operator is used
                            'foodics_count_id': count['id'],
                            'foodics_count_reference': count['reference'],
                            'foodics_count_date': count['business_date'] # shows error if member access operator is used
                        }

                        stock_adjust_record = self.sudo().create(vals)
                        self.env.cr.commit()
                        stock_adjust_record.action_apply_inventory()
                        self.env.cr.commit()
                        # stock_record_ids.append(stock_adjust_record.id)
                
                # batch-apply adjustment records after loop has ended
                # quants = self.env['stock.quant'].search([('foodics_count_id', '=', count['id'])])
                # wizard = self.env['stock.inventory.adjustment.name'].create({
                #     'inventory_adjustment_name': f"{count['reference']}",
                #     'quant_ids': [(6, 0, stock_record_ids)]})
                # wizard.action_apply()

        except Exception as e:
            _logger.error(e)
            self.env.cr.rollback()
            raise UserError((f"Something went wrong while creating/updating inventory counts in Odoo!\nHere's the technical details of what happened:\n{e}"))


'''
ai-generated
https://www.odoo.com/documentation/16.0/applications/inventory_and_mrp/inventory/warehouses_storage/inventory_management/count_products.html
https://www.cybrosys.com/blog/how-to-add-opening-stock-and-adjusting-stock-in-odoo-16
https://www.cybrosys.com/odoo/odoo-books/odoo-book-v16/inventory/inventory-adjustment/
# Import the Odoo API
from odoo import api, fields, models

# Create a new inventory adjustment
inventory = self.env['stock.inventory'].create({
    'name': 'New Inventory Adjustment',
    'product_id': False, # Leave this as False to adjust all products
    'location_id': self.env.ref('stock.stock_location_stock').id, # Use the ID of the WH/Stock location
    'filter': 'product', # Use 'product' as the filter to adjust products by category
    'category_id': self.env.ref('product.product_category_all').id, # Use the ID of the All category
})

# Confirm the inventory adjustment
inventory.action_start()
odoo-bin --test-file addons/purchase_stock/tests/test_purchase_order.py --test-enable
# Optionally, you can set the counted quantities for each product line
# For example, to set the counted quantity of the product "iPad Retina Display" to 10, use the following code:
inventory.line_ids.filtered(lambda l: l.product_id.name == 'iPad Retina Display').product_qty = 10

# Validate the inventory adjustment
inventory.action_validate()

'''