# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError
import base64
import requests
import logging



_logger = logging.getLogger(__name__)
class ProductVariant(models.Model):
    _inherit = 'product.product'

    foodics_item_id = fields.Char('Foodic Item ID', index=True, related="product_tmpl_id.foodics_item_id", store=True, copy=True)


class ProductProduct(models.Model):
    _inherit = 'product.template'

    name_localized = fields.Char('Name Localized')
    foodics_item_id = fields.Char('Foodic Item ID') # was foodic_product_id 
    # TODO don't forget to modify the field name in the view
    is_modifier = fields.Boolean()


    def set_products_to_odoo(self, res):
        ProductProduct = self.env['product.template']
        for product in res.get('data'):
            image = False
            try:
                if product.get('image'):
                    image = base64.b64encode(requests.get(product.get('image').strip()).content).replace(b'\n', b'')
            except:
                pass

            if product.get('cost') == None:
                product.update({'cost': 0.0})

            vals = {
                'foodics_item_id': product.get('id'),
                'default_code': product.get('sku'),
                'name': product.get('name'),
                'name_localized': product.get('name_localized'),
                'description': product.get('description'),
                'image_1920': image,
                'type': 'product' if product.get('is_stock_product') else 'consu',
                'list_price': product.get('price'),
                'standard_price': product.get('cost'),
                'available_in_pos': True,
                'sale_ok': True,
                'active': True,
            }

            if product.get('deleted_at'):
                vals['active'] = False

            if product.get('status') == 5:
                vals['active'] = False

            if self.env.context.get('is_modifier'):
                vals['is_modifier'] = True
            product_id = ProductProduct.search([('foodics_item_id', '=', product.get('id')), ('active', 'in', [True, False])], limit=1)
            if not product_id:
                product_id = ProductProduct.create(vals)
            barcode = product.get('barcode')
            if barcode:
                prdt_with_barcode = self.search([('barcode', '=', barcode), ('active', 'in', [True, False])])
                if not prdt_with_barcode:
                    product_id.barcode = barcode
        self._cr.commit()





    def process_storage_and_ingredient_UoM(self, inventory_item):
        kilogram_list = ['kg', 'kgs', 'k.g', 'k.g.', 'kilogram', 'kilograms', 'kilog.', 'kgm', 'k.gm.']
        gram_list = ['g', 'gs', 'g.', 'gm.', 'gram', 'grams', 'g.m.', 'gms', 'g.m.s', 'g.m.s.']
        litre_list = ['l', 'ls', 'l.', 'liter', 'litter', 'litters', 'liters', 'litre', 'litres', 'littre', 'littres', 'ltr', 'ltrs', 'ltr.']

        try:
            if inventory_item['storage_unit'].lower() == inventory_item['ingredient_unit'].lower():
                if inventory_item['ingredient_unit'].lower() in kilogram_list:
                    storage_uom_id = 12
                    ingredient_uom_id = 12
                elif inventory_item['ingredient_unit'].lower() in gram_list:
                    storage_uom_id = 13
                    ingredient_uom_id = 13
                elif inventory_item['ingredient_unit'].lower() in litre_list:
                    storage_uom_id = 10
                    ingredient_uom_id = 10

                else:
                    storage_uom_id = 1
                    ingredient_uom_id = 1
                    
                
            else:
                if inventory_item['storage_unit'].lower() in kilogram_list:
                    storage_uom_id = 12
                elif inventory_item['storage_unit'].lower() in gram_list:
                    storage_uom_id = 13
                elif inventory_item['storage_unit'].lower() in litre_list:
                    storage_uom_id = 10
                # elif inventory_item['storage_unit'].lower() in ['ml', 'mls', 'ml.', 'm.l.', 'm.l', 'milliliter', 'millilitter', 'millilitters', 'milliliters', 'millilitre', 'millilitres', 'millilittre', 'mililiter', 'mililitter', 'mililitters', 'mililiters', 'mililitre', 'mililitres', 'mililittre', 'mltr', 'mlltr', 'ml.ltr', 'mlltrs', 'm.l.ltr.']:
                #     storage_uom_id = 10 # test null in requests reponse using type() in idle and continue unit lists from ml
                else:
                    storage_uom_id = 1

                if inventory_item['ingredient_unit'].lower() in kilogram_list:
                    ingredient_uom_id = 12
                elif inventory_item['ingredient_unit'].lower() in gram_list:
                    ingredient_uom_id = 13
                elif inventory_item['ingredient_unit'].lower() in litre_list:
                    ingredient_uom_id = 10
                # elif inventory_item['ingredient_unit'].lower() in ['ml', 'mls', 'ml.', 'm.l.', 'm.l', 'milliliter', 'millilitter', 'millilitters', 'milliliters', 'millilitre', 'millilitres', 'millilittre', 'mililiter', 'mililitter', 'mililitters', 'mililiters', 'mililitre', 'mililitres', 'mililittre', 'mltr', 'mlltr', 'ml.ltr', 'mlltrs', 'm.l.ltr.']:
                #     ingredient_uom_id = 10 # test null in requests reponse using type() in idle and continue unit lists from ml
                else:
                    ingredient_uom_id = 1
            return (storage_uom_id, ingredient_uom_id)
        except:
            raise UserError(_('Something went wrong while processing units of measure (UoM) for storable inventory items in Odoo!'))
            '''string.lower()
            {kg: [KG, KGS, Kilograms, Kilogram, KILOGRAMS, k.g],
            g: [g, GMS, GM, gm.], # TODO
            Units: [p, p., pc, pc., p.c, PCS, PKGS, PKG, PKT, unit, pieces, EA, box, btl or anything else],
            l: [LTR, liter, litre, liters, litres]}'''


    def set_consumable_foodics_product_to_odoo(self, res):
        # storable invent items and consumable products has been fused to avoid api requests limiting behaviour and decrease consumed time
        try:
            # with self.pool.cursor() as new_cr:
            # self = self.with_env(self.env(cr=new_cr))
            ProductModel = self.env['product.template']
            ProductCategory = self.env['product.category']
            ManunfacturingBoMLineModel = self.env['mrp.bom.line']
            try:
                for product in res['data']: # product is a dict
                    #######################
                    try:
                        for item in product['ingredients']:
                            # every item in this inner loop must be replaced with ingredient
                                
                            storage_UoM_id, ingredient_UoM_id = 1, 1
                            # associate only the required fields
                            vals = {
                                
                                'categ_id': 2,
                                'detailed_type': 'product' if not item['is_product'] else 'consu',
                                'name': item['name'] if item['name'] else False,
                                
                                'purchase_line_warn': 'no-message',
                                'sale_line_warn': 'no-message',
                                'uom_id': ingredient_UoM_id, 
                                'uom_po_id': ingredient_UoM_id,

                                'foodics_item_id': item['id'],
                                'default_code': False if item['sku'] is None else item['sku'],
                                'barcode': item['barcode'] if item['barcode'] else False,
                                'name_localized': item['name_localized'] if item['name_localized'] else False,
                                
                                
                                
                                'list_price': item['cost'],
                                'standard_price': item['cost'],
                                'available_in_pos': False,
                                'sale_ok': True,
                                'active': True,
                                }
                            if item['deleted_at']:
                                vals['active'] = False
                            item_id = ProductModel.sudo().search([('foodics_item_id', '=', item['id'])], limit=1)
                            if item_id:
                                if ((item_id.name != item['name']) or (item_id.name_localized != item['name_localized']) or (item_id.default_code != item['sku']) or (item_id.barcode != item['barcode']) or (item_id.standard_price != item['cost']) or (item_id.list_price != item['cost'])):
                                    item_id.update(vals)
                                    _logger.info("updated a storable")
                                else:
                                    continue
                            else:
                                ProductModel.sudo().create(vals)
                        # new_cr.commit()
                        self._cr.commit()

                    except Exception as e:
                        raise UserError((f"Something went wrong while creating/updating storable inventory items in Odoo!\nPlease try again later\nHere's the technical details of what happened:\n{e}"))

                    #########

                    
                    if (product['category']['name']) and (ProductCategory.sudo().search([('name', '=', product['category']['name'])], limit=1)):
                        cat_id = ProductCategory.sudo().search([('name', '=', product['category']['name'])], limit=1).id
                    else:
                        ProductCategory.sudo().create({'name': product['category']['name'],
                                                            'parent_id': 2,
                                                            'property_cost_method': 'standard',
                                                            'property_valuation': 'manual_periodic'})
                        cat_id = ProductCategory.sudo().search([('name', '=', product['category']['name'])], limit=1).id
                    
                    storage_UoM_id, ingredient_UoM_id = 1, 1
                    vals = {
                        'categ_id': cat_id,
                        'detailed_type': 'consu' if not product['is_stock_product'] else 'product',
                        'name': product['name'] if product['name'] else False,
                        
                        'purchase_line_warn': 'no-message',
                        'sale_line_warn': 'no-message',
                        'uom_id': ingredient_UoM_id,
                        'uom_po_id': storage_UoM_id,

                        'foodics_item_id': product['id'],
                        'default_code': False if product['sku'] is None else product['sku'],
                        'barcode': product['barcode'] if product['barcode'] else False,
                        'name_localized': product['name_localized'] if product['name_localized'] else False,
                        'description': f"<p>{product['description']}</p>\n<p>{product['description_localized']}</p>" if (product['description'] or product['description_localized']) else False,
                        
                        
                        'list_price': product['price'] if product['price'] else 0,
                        'standard_price': product['cost'] if product['cost'] else 0,
                        'to_weight': True if product['selling_method'] == 2 else False,
                        'available_in_pos': True,
                        'sale_ok': True,
                        'purchase_ok': product['is_stock_product'],
                        'produce_delay': product['preparation_time'] if product['preparation_time'] else 0,
                        'active': True,
                        
                        }
                    try:
                        if product['image']: # json null translates to None in python and is not equivalent to False. But (if test) somehow manages to differentiate between null value and anything else
                            image = base64.b64encode(requests.get(product['image'].strip()).content).replace(b'\n', b'')
                            if image:
                                vals['image_1920'] = image

                    except:
                        pass
                    if product['deleted_at']:
                        vals['active'] = False
                    
                    product_id = ProductModel.sudo().search([('foodics_item_id', '=', product['id'])], limit=1)
                    if product_id:
                        if ((product_id.name != product['name']) or (product_id.name_localized != product['name_localized']) or (product_id.default_code != product['sku']) or (product_id.barcode != product['barcode']) or (product_id.list_price != product['price']) or (product_id.active != vals['active'])):
                            product_id.update(vals)
                            _logger.info("updated a consumable")
                        else:
                            continue
                    else:
                        ProductModel.sudo().create(vals)
                    # new_cr.commit()
                    self._cr.commit()
                    ManunfacturingBoMLineModel.set_ingredients_as_BoM_in_odoo(res)
            except Exception as e:
                raise UserError(f"Something went wrong while creating/updating consumable products in Odoo!\nPlease try again later\nHere's the technical details of what happened:\n{e}")
        except Exception as f:
            raise UserError(f"{f}")
class MRPBoMLine(models.Model):
    _inherit = 'mrp.bom.line'

    foodics_item_id = fields.Char('Foodic Item Id') # was foodic_product_id

    def set_ingredients_as_BoM_in_odoo(self, res):
        # create BoM then create BoM lines by searching by product template foodics_item_id
        try:
            # with self.pool.cursor() as new_cr:
            # self = self.with_env(self.env(cr=new_cr))

            ProductModel = self.env['product.template']
            ManunfacturingBoMModel = self.env['mrp.bom']
            ManunfacturingBoMLineModel = self.env['mrp.bom.line']

            for product in res['data']:
                ingredient_stored_data = ProductModel.sudo().search([('foodics_item_id', 'in', [ing['id'] for ing in product['ingredients']])])
                product_stored_data = ProductModel.sudo().search([('foodics_item_id', '=', product['id'])], limit=1)
                if product_stored_data and ingredient_stored_data:
                    if product['ingredients']:


                        vals = {
                            'code': product['id'],
                            'consumption': 'strict',
                            'product_tmpl_id': product_stored_data.id,
                            'product_qty': 1,
                            'ready_to_produce': 'all_available',
                            'type': 'normal'
                            }
                        
                        
                        
                        bom_stored_data = ManunfacturingBoMModel.sudo().search([('product_tmpl_id', '=', product_stored_data.id)], limit=1)
                        if bom_stored_data:
                            if (bom_stored_data.product_tmpl_id.name != product['name']
                            or (bom_stored_data.product_tmpl_id.name_localized != product['name_localized'])
                            or (bom_stored_data.product_tmpl_id.default_code != product['sku'])
                            or (bom_stored_data.product_tmpl_id.barcode != product['barcode'])
                            or (bom_stored_data.product_tmpl_id.list_price != product['price'])):
                                bom_stored_data.update(vals)
                            for ingredient in product['ingredients']:

                                vals = {
                                    'product_id': self.env['product.product'].sudo().search([('foodics_item_id', '=', ingredient['id'])], limit=1).id, #############
                                    'product_tmpl_id': self.env['product.template'].sudo().search([('foodics_item_id', '=', ingredient['id'])], limit=1).id,
                                    'product_qty': ingredient['pivot']['quantity'],
                                    'product_uom_id': 1,
                                    'bom_id': bom_stored_data.id,
                                    'foodics_item_id': ingredient['id']}
                                bom_line = ManunfacturingBoMLineModel.sudo().search([('foodics_item_id', '=', ingredient['id'])], limit=1)
                                if bom_line:
                                    if (bom_line.product_qty != ingredient['pivot']['quantity']):
                                        bom_line.update(vals)
                                    else:
                                        pass
                                else:
                                    ManunfacturingBoMLineModel.create(vals)
                                    # maybe update bom model if products doesn't show lines
                            
                        else:
                            new_bom = ManunfacturingBoMModel.sudo().create(vals) ############
                            for ingredient in product['ingredients']:
                                vals = {
                                    'product_id': self.env['product.product'].sudo().search([('foodics_item_id', '=', ingredient['id'])], limit=1).id,
                                    'product_tmpl_id': self.env['product.template'].sudo().search([('foodics_item_id', '=', ingredient['id'])], limit=1).id,
                                    'product_qty': ingredient['pivot']['quantity'],
                                    'product_uom_id': 1,
                                    'bom_id': new_bom.id, #####
                                    'foodics_item_id': ingredient['id']}
                                ManunfacturingBoMLineModel.create(vals) ############
                                
                # new_cr.commit()
                self._cr.commit()

        except Exception as e:
            raise UserError((f"Something went wrong while creating/updating BoM in Odoo!\nHere's the technical details of what happened:\n{e}"))


