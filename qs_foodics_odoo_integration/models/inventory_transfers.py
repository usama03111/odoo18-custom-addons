from odoo import fields, models, _
import logging
import asyncio
import aiohttp


_logger = logging.getLogger(__name__)

class InventTransfers(models.Model):
    _inherit = 'stock.picking'

    foodics_transaction_id = fields.Char('Foodics Transaction ID')

    def set_transaction_to_odoo(self, res):
        _logger.info('called the transfers method')
        InventoryLocation = self.env['stock.location']
        Product = self.env['product.product']

        try:
            for trnsct in (res.get('data')):
                print(trnsct['id'])

                transfer_stored_data = self.env['stock.picking'].search([('foodics_transaction_id', '=', trnsct['id'])], limit=1)

                if transfer_stored_data:
                    status_dict = {1: 'draft', 2: 'confirmed', 3: 'cancel', 4: 'assigned'}
                    if status_dict[trnsct['status']] != transfer_stored_data.state:
                        if ((transfer_stored_data.state == 'done') and (trnsct['status'] == 4)):
                            continue
                        elif (((transfer_stored_data.state == 'done') or (transfer_stored_data.state == 'assigned') or (transfer_stored_data.state == 'confirmed') or (transfer_stored_data.state == 'draft')) and (trnsct['status'] == 3)):
                            
                            transfer_stored_data.action_cancel()
                        elif (((transfer_stored_data.state == 'done') or (transfer_stored_data.state == 'assigned') or (transfer_stored_data.state == 'confirmed') or (transfer_stored_data.state == 'draft')) and (trnsct['status'] == 2)):
                            transfer_stored_data.action_cancel()
                            transfer_stored_data.action_confirm()

                
                        else:
                            continue
                                
                else:
                    location_stored_data = InventoryLocation.sudo().search([('foodics_branch_id', '=', trnsct['branch']['id'])], limit=1)
                    dest_location_stored_data = InventoryLocation.sudo().search([('foodics_branch_id', '=', trnsct['other_branch']['id'])], limit=1)
                    if not location_stored_data:
                        InventoryLocation.create({
                'foodics_branch_id': trnsct['branch']['id'],
                'name': trnsct['branch']['name'],
                'usage': "internal"
                # check with implementors if they need other options to be checked such as replinshment
                })
                    if not dest_location_stored_data:
                        InventoryLocation.create({
                'foodics_branch_id': trnsct['other_branch']['id'],
                'name': trnsct['other_branch']['name'],
                'usage': "internal"
                # check with implementors if they need other options to be checked such as replinshment
                })
                    vals = {
                        'foodics_transaction_id': trnsct.get('id'),
                        'location_id': InventoryLocation.sudo().search([('foodics_branch_id', '=', trnsct['branch']['id'])], limit=1).id,
                        'location_dest_id': InventoryLocation.sudo().search([('foodics_branch_id', '=', trnsct['other_branch']['id'])], limit=1).id,
                        'picking_type_id': 5,
                        'move_type': 'direct'
                        # check with implementors if they need other options to be checked such as replinshment
                        }
                    
                    if vals['location_dest_id'] == None:
                        continue
                    
                    if ((trnsct['status'] == 4) and (trnsct['other_transaction']['status'] == 4) and (trnsct['other_transaction']['type'] == 6)):
                        
                        created_move = self.env['stock.picking'].create(vals)


                        

                        print(self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1))
                        move_lines = self.env['stock.move'].sudo().search([('picking_id', '=', created_move.id)])
                        if move_lines:
                            pass
                        else:
                            for line in trnsct['items']:
                                if not Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1):
                                    
                                    vals = {
                                    'categ_id': 2,
                                    'detailed_type': 'product' if not line['is_product'] else 'consu',
                                    'name': line['name'] if line['name'] else False,
                                    'purchase_line_warn': 'no-message',
                                    'sale_line_warn': 'no-message',
                                    'uom_id': 1, 
                                    'uom_po_id': 1,

                                    'foodics_item_id': line['id'],
                                    'default_code': False if line['sku'] is None else line['sku'],
                                    'barcode': line['barcode'] if line['barcode'] else False,
                                    'name_localized': line['name_localized'] if line['name_localized'] else False,
                                    'list_price': line['cost'],
                                    'standard_price': line['cost'],
                                    'available_in_pos': False,
                                    'sale_ok': True,
                                    'active': True,
                                    }
                                    if line['deleted_at']:
                                        vals['active'] = False

                                    self.env['product.template'].sudo().create(vals)
                                    self.env.cr.commit()

                                    print("validated")
                                    vals = {'name': created_move.name,
                                            'picking_id': self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1).id,
                                            
                                            'product_id': Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1).id,
                                            'location_id': location_stored_data.id,
                                            'location_dest_id': dest_location_stored_data.id,
                                            'product_uom': 1,
                                            
                                            'product_uom_qty': line['pivot']['quantity'],
                                            'quantity_done': line['pivot']['quantity']}
                                    self.env['stock.move'].sudo().create(vals)
                                    print("validated")
                                    
                                else:

                                    print("validated")
                                    vals = {'name': created_move.name,
                                            'picking_id': self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1).id,
                                            
                                            'product_id': Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1).id,
                                            'location_id': location_stored_data.id,
                                            'location_dest_id': dest_location_stored_data.id,
                                            'product_uom': 1,
                                            
                                            'product_uom_qty': line['pivot']['quantity'],
                                            'quantity_done': line['pivot']['quantity']}
                                    self.env['stock.move'].sudo().create(vals)
                                    print("validated")
                            self.env.cr.commit()

                            created_move.action_confirm()
                            created_move.scheduled_date = trnsct['created_at']
                            created_move.button_validate()
                            created_move.date_done = trnsct['updated_at']
                    else:
                        
                        if ((trnsct['status'] == 3) and (trnsct['other_transaction']['status'] == 4) and (trnsct['other_transaction']['type'] == 6)):
                            created_move = self.env['stock.picking'].create(vals)




                            

                            print(self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1))
                            move_lines = self.env['stock.move'].sudo().search([('picking_id', '=', created_move.id)])
                            if move_lines:
                                pass
                            else:
                                for line in trnsct['items']:
                                    if not Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1):
                                        
                                        vals = {
                                        'categ_id': 2,
                                        'detailed_type': 'product' if not line['is_product'] else 'consu',
                                        'name': line['name'] if line['name'] else False,
                                        'purchase_line_warn': 'no-message',
                                        'sale_line_warn': 'no-message',
                                        'uom_id': 1, 
                                        'uom_po_id': 1,

                                        'foodics_item_id': line['id'],
                                        'default_code': False if line['sku'] is None else line['sku'],
                                        'barcode': line['barcode'] if line['barcode'] else False,
                                        'name_localized': line['name_localized'] if line['name_localized'] else False,
                                        'list_price': line['cost'],
                                        'standard_price': line['cost'],
                                        'available_in_pos': False,
                                        'sale_ok': True,
                                        'active': True,
                                        }
                                        if line['deleted_at']:
                                            vals['active'] = False

                                        self.env['product.template'].sudo().create(vals)
                                        self.env.cr.commit()
                                        
                                        print("cancelled")
                                        vals = {'name': created_move.name,
                                                'picking_id': self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1).id,
                                                
                                                'product_id': Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1).id,
                                                'location_id': location_stored_data.id,
                                                'location_dest_id': dest_location_stored_data.id,
                                                'product_uom': 1,
                                                
                                                'product_uom_qty': line['pivot']['quantity'],
                                                'quantity_done': line['pivot']['quantity']}
                                        self.env['stock.move'].sudo().create(vals)
                                        print("cancelled")

                                    else:

                                        print("cancelled")
                                        vals = {'name': created_move.name,
                                                'picking_id': self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1).id,
                                                
                                                'product_id': Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1).id,
                                                'location_id': location_stored_data.id,
                                                'location_dest_id': dest_location_stored_data.id,
                                                'product_uom': 1,
                                                
                                                'product_uom_qty': line['pivot']['quantity'],
                                                'quantity_done': line['pivot']['quantity']}
                                        self.env['stock.move'].sudo().create(vals)
                                        print("cancelled")
                                self.env.cr.commit()

                                created_move.scheduled_date = trnsct['created_at']
                                created_move.action_cancel()



                        elif (((trnsct['status'] == 2)) and ((trnsct['other_transaction']['status'] == 2) or (trnsct['other_transaction']['status'] == 4)) and (trnsct['other_transaction']['type'] == 6)):
                            created_move = self.env['stock.picking'].create(vals)




                            

                            print(self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1))
                            move_lines = self.env['stock.move'].sudo().search([('picking_id', '=', created_move.id)])
                            if move_lines:
                                pass
                            else:
                                for line in trnsct['items']:
                                    if not Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1):
                                        
                                        vals = {
                                        'categ_id': 2,
                                        'detailed_type': 'product' if not line['is_product'] else 'consu',
                                        'name': line['name'] if line['name'] else False,
                                        'purchase_line_warn': 'no-message',
                                        'sale_line_warn': 'no-message',
                                        'uom_id': 1, 
                                        'uom_po_id': 1,

                                        'foodics_item_id': line['id'],
                                        'default_code': False if line['sku'] is None else line['sku'],
                                        'barcode': line['barcode'] if line['barcode'] else False,
                                        'name_localized': line['name_localized'] if line['name_localized'] else False,
                                        'list_price': line['cost'],
                                        'standard_price': line['cost'],
                                        'available_in_pos': False,
                                        'sale_ok': True,
                                        'active': True,
                                        }
                                        if line['deleted_at']:
                                            vals['active'] = False

                                        self.env['product.template'].sudo().create(vals)
                                        self.env.cr.commit()
                                        
                                        print("assigned")
                                        vals = {'name': created_move.name,
                                                'picking_id': self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1).id,
                                                
                                                'product_id': Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1).id,
                                                'location_id': location_stored_data.id,
                                                'location_dest_id': dest_location_stored_data.id,
                                                'product_uom': 1,
                                                
                                                'product_uom_qty': line['pivot']['quantity'],
                                                'quantity_done': line['pivot']['quantity']}
                                        self.env['stock.move'].sudo().create(vals)
                                        print("assigned")

                                    else:

                                        print("assigned")
                                        vals = {'name': created_move.name,
                                                'picking_id': self.env['stock.picking'].sudo().search([('foodics_transaction_id', '=', trnsct['id'])], limit=1).id,
                                                
                                                'product_id': Product.sudo().search([('foodics_item_id', '=', line['id'])], limit=1).id,
                                                'location_id': location_stored_data.id,
                                                'location_dest_id': dest_location_stored_data.id,
                                                'product_uom': 1,
                                                
                                                'product_uom_qty': line['pivot']['quantity'],
                                                'quantity_done': line['pivot']['quantity']}
                                        self.env['stock.move'].sudo().create(vals)
                                        print("assigned")
                                self.env.cr.commit()


                                created_move.scheduled_date = trnsct['created_at']

        except Exception as e:
            _logger.error(e)
            self.env.cr.rollback()

