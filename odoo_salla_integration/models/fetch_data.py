# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from logging import getLogger
_logger = getLogger(__name__)
from odoo.addons.odoo_multi_channel_sale.tools import remove_tags

class FetchData:
    def __init__(self, channel_id, **kw):
        self.channel_id = channel_id
        self.id = channel_id.id
        self.env = channel_id.env

    def get_all_categories(self, data):
        category_vals = []
        for val in data:
            category_vals.append(
                self.category_for_category(val))
        for val in data:
            if val.get('items'):
                category_vals.extend(self.get_all_categories(
                    val.get('items')))
        return category_vals

    def category_for_category(self, data):
        category_vals = ({
            "channel_id": self.channel_id.id,
            "channel": self.channel_id.channel,
            "leaf_category": False if data.get('items') else True,
            "parent_id": data.get('parent_id') or False,
            "store_id": data.get('id'),
            "name": data.get('name')
        })
        return category_vals

    def get_shipping_vals(self, channel_id, shipping_data):
        return {
            "name": shipping_data.get("name"),
            "store_id": shipping_data.get("id"),
            "shipping_carrier": shipping_data.get("name"),
            "channel_id": channel_id.id,
            "channel": channel_id.channel,
            "description": shipping_data.get("activation_type", False)
        }

    def process_customer(self, customer):
        customer_data = {
            'channel_id': self.channel_id.id,
            'store_id': customer.get('id'),
            'name': customer.get('first_name', False),
            'last_name':customer.get('last_name', False),
            'email': customer.get('email'),
            'mobile': customer.get('mobile'),
            'city': customer.get('city'),
            'street': customer.get('location', False),
            'country_code': customer.get('country_code') if customer.get('country_code') else customer.get('country'),
            'website': customer.get('urls').get('customer') if customer.get('urls') else False
        }
        address_data_list = []
        customer_data['contacts'] = address_data_list
        return customer_data

    def process_address(self, order, store_partner_id, type=False):
        contacts = {}
        billing_address = []
        email = order.get('customer').get('email')
        name = order.get('customer').get('first_name')+ " "+ order.get('customer').get('last_name')
        phone = order.get('customer').get('mobile')

        address = order.get('shipments', {})
        if isinstance(address, list):
            address = address[0]
            if isinstance(address, list):
                address = address[0]
            billing_address = address.get('ship_to', {})
            if billing_address:
                name = billing_address.get('name')
                phone = billing_address.get('phone')
        if not billing_address and order.get('shipping'):
            billing_address = order.get('shipping').get('address')
            receiver_data = order.get('shipping').get('receiver', {})
            if receiver_data and isinstance(receiver_data, dict):   
                name = receiver_data.get('name') if receiver_data.get('name') else name
                email = receiver_data.get('email') if receiver_data.get('email') else email
                phone = receiver_data.get('phone') if receiver_data.get('phone') else phone
        if billing_address:
            contacts.update({
                'invoice_partner_id': f'billing_{store_partner_id}' if store_partner_id else email,
                'invoice_name': name,
                'invoice_email':  email,
                'invoice_phone': phone,
                'invoice_street': billing_address.get('street_number'),
                'invoice_street2': billing_address.get('shipping_address') or billing_address.get('address_line'),
                'invoice_zip': billing_address.get('postal_code'),
                'invoice_city': billing_address.get('city'),
                'invoice_country_code': billing_address.get('country_code') or False,
                'same_shipping_billing': True
            })
        return contacts

    def import_product_vals(self, product):
        vals = self.get_product_basic_vals(product)
        if product.get('options'):
            variants, options = self.get_variant_vals(product)
            vals.update(
                {'variants': variants, 'salla_product_attribute_options': options})
        return vals

    def get_product_basic_vals(self, product):
        return {
            'store_id': product.get('id'),
            'name': product.get('name'),
            'channel_id': self.id,
            'channel': self.channel_id.channel,
            'description_sale': remove_tags(product.get('description')),
            'description': product.get('promotion').get('sub_title'),
            'image_url': product.get('main_image'),
            'list_price': product.get("price").get('amount'),
            'weight': product.get("weight"),
            'wk_default_code': product.get("sku"),
            'default_code': product.get("sku"),
            'qty_available': product.get("quantity"),
            'extra_categ_ids': ",".join([str(x.get('id')) for x in product.get('categories')]) if product.get('categories') else False
        }

    def get_variant_vals(self, product):
        options = self.get_product_options(product.get('options'))
        variants = []
        salla_product_attribute_option_vals = {}
        for variant in product.get('skus'):
            salla_options = variant.get('related_option_values')
            if salla_options:
                salla_options.sort()
                salla_product_attribute_option_vals.update(
                    {"_".join(map(str, salla_options)): variant.get('id')})
            if options:
                name_value = [{
                    'name': options.get(attribute_id).get('name'),
                    'value': options.get(attribute_id).get('value_name'),
                } for attribute_id in variant.get('related_option_values')]
            variants.append({
                'default_code': variant.get('sku'),
                'barcode': variant.get('barcode'),
                'store_id': variant.get('id'),
                'qty_available': variant.get('stock_quantity'),
                'list_price': variant.get('price').get('amount'),
                'weight': variant.get('weight'),
                # 'image_url': image_url,
                'name_value': name_value,
            })
        return variants, salla_product_attribute_option_vals or False

    def get_product_options(self, options):
        """
            options will be : 
            {
                value_id1: {option_name:name, option_id: id, value_name: value_name},
                value_id2: {option_name:name, option_id: id, value_name: value_name},
                ...
            }
        """
        option_vals = {}
        for option in options:
            for value in option.get('values'):
                option_vals.update({value.get('id'): {'name': option.get(
                    'name'), 'id': option.get('id'), 'value_name': value.get('name')}})
        return option_vals

    def process_order(self, order):
        order_data = {
            'channel_id': self.id,
            'store_id': order.get('id'),
            'name': str(order.get('reference_id')),
            'currency': order.get('currency'),
            'date_order': order.get('date').get('date'),
            'order_state': order.get('status').get('slug'),
            'line_type': 'multi'
        }
        if order.get('payment_method'):
            order_data.update(payment_method=order.get('payment_method'))
        if order.get('shipping') or order.get('shipments'):
            if type(order.get('shipping')) == dict:
                order_data.update(
                    {'carrier_id': order.get('shipping').get('company')})
            elif type(order.get('shipments')) == dict:
                order_data.update(
                    {'carrier_id': order.get('shipments').get('courier_name')})
        if order.get('customer'):
            customer = order.get('customer')
            order_data.update(
                {
                    'partner_id': customer.get('id'),
                    'customer_name': customer.get('first_name')+' '+customer.get('last_name'),
                    'customer_email': customer.get('email'),
                    'customer_mobile': customer.get('mobile'),
                    'customer_phone': customer.get('mobile'),
                }
            )
            contacts = self.process_address(order, customer.get('id'))
            order_data.update(contacts)
        order_lines = [(5, 0)]
        for line in order.get("items"):
            line_product_id = line.get("product").get("id")
            exists = self.channel_id.match_product_mappings(line_product_id)
            attribute_options = False
            if not exists:
                #Update or create product feed only if there is no mapping exists
                attribute_options = self.create_product_feed(line_product_id)
            order_line_data = {
                'line_name': line.get("name"),
                'line_product_id': line_product_id,
                'line_variant_ids': "No Variants" if not line.get("options") else self.get_variant_id(line, attribute_options),
                'line_price_unit': line.get("amounts").get("price_without_tax").get("amount"),
                'line_product_uom_qty': line.get("quantity"),
                'line_product_default_code': line.get("sku", False),
                'line_taxes': self.process_tax(line.get("amounts").get("tax")),
            }
            order_lines.append((0, 0, order_line_data))
        # Discount Line
        order_dicounts = order.get('amounts').get('discounts')
        if order_dicounts:
            for discount in order_dicounts:
                if discount.get('discount') != '0':
                    discount_line_data = {
                        'line_name': 'Discount: {}'.format(discount.get('title') or discount.get('code')),
                        'line_price_unit': float(discount.get('discount')),
                        'line_product_uom_qty': 1,
                        'line_source': 'discount',
                        'line_taxes': self.process_tax(order.get("amounts").get("tax")),
                    }   
                order_lines.append((0, 0, discount_line_data))
        # Delivery Line
        if order.get('amounts').get('shipping_cost'):
            if order.get('amounts').get('shipping_cost', {}).get('amount'):
                order_lines.append((0,0,{
                    'line_name': 'Delivery',
                    'line_price_unit': order.get('amounts').get('shipping_cost', {}).get('amount'),
                    'line_product_uom_qty': 1,
                    'line_taxes': self.process_tax(order.get("amounts").get("tax")),
                    'line_source': 'delivery',
                }))
        order_data['line_ids'] = order_lines
        return order_data

    def get_variant_id(self, order_line_product, attribute_options=False):
        option_vals = []
        for rec in order_line_product.get("options"):
            option_vals.append(rec.get("value").get("id"))
        option_vals.sort()
        value = "_".join(map(str, option_vals))
        mappings = self.channel_id.match_template_mappings(
            store_product_id=order_line_product.get("product").get("id"))
        if mappings:
            template_id = mappings.template_name
            if template_id:
                if template_id.salla_product_attribute_options:
                    options = eval(template_id.salla_product_attribute_options)
                    return options.get(value)
        elif attribute_options:
            return eval(attribute_options).get(value)
        return False

    def process_tax(self, tax):
        if tax and tax.get("amount").get("amount"):            
            return [
                {
                    'included_in_price': False,
                    'name': f"Salla Tax {tax.get('percent')}%",
                    'rate': tax.get('percent'),
                    'tax_type': 'percent'
                }
            ]
        else:
            return False

    def create_product_feed(self, object_id): # orders item
        try:
            kw = dict(
                filter_type='id',
                object_id=object_id
            )
            values, kw = self.channel_id.get_sallaApi().get_products(**kw)
            if values:
                vals = values[0]
                if vals.get('variants'):
                    variants = vals.pop('variants')
                    feed_variants = [(0, 0, variant) for variant in variants]
                    vals.update(feed_variants=feed_variants)
                feed = self.channel_id.match_product_feeds(object_id)
                if not feed: #create product feed
                    feed = self.env['product.feed'].create(vals)
                else:
                    if vals.get('feed_variants'): #update product feed
                        vals['feed_variants'].insert(0, (5, 0))
                    feed.write(vals)
                return feed.salla_product_attribute_options
        except Exception as e:
            _logger.error('Error occurred %r',e, exc_info=True)            
        return False
