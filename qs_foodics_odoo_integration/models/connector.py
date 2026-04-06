import requests
import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json
import logging
import time
from dateutil.relativedelta import relativedelta
import asyncio

import aiohttp

_logger = logging.getLogger(__name__)


class FoodicsConnector(models.Model):
    _name = 'foodics.connector'
    _rec_name = 'business_name'
    _description = "Foodics Connector"

    business_name = fields.Char(string='Business', readonly=True)
    user_name = fields.Char(string='User', readonly=True, copy=False)
    email = fields.Char(readonly=True, copy=False)
    order_date = fields.Date()
    access_token = fields.Char(string='Access Token', required=True)

    from_date = fields.Date(string='Last POS Order Imported Date')
    last_purchase_order_import_date = fields.Date(string='Last Purchase Order Imported Date')
    to_date = fields.Date(string='To Date')
    state = fields.Selection([('authenticate', 'Authenticate'), ('authenticated', 'Authenticated')],
                             default='authenticate', copy=False)
    page = fields.Integer(default=1)
    note = fields.Text()
    environment = fields.Selection([('sandbox', 'Sandbox'), ('production', 'Production')], required=True,
                                   default='production')
    url = fields.Char(compute='set_foodics_url')
    products_with_ingredients = fields.Text()

    @api.depends('environment')
    def set_foodics_url(self):
        for rec in self:
            if rec.environment == 'sandbox':
                rec.url = 'https://api-sandbox.foodics.com'
            else:
                rec.url = 'https://api.foodics.com'

    def foodics_whoami(self):
        res = self.foodic_import_data(self.url + '/v5/whoami')
        if not res or not res.get('data'):
            raise UserError(_("Invalid response from Foodics whoami endpoint"))
        self.business_name = res.get('data').get('business').get('name')
        self.user_name = res.get('data').get('user').get('name')
        self.email = res.get('data').get('user').get('email')
        self.state = 'authenticated'

    def authenticate(self):
        self.foodics_whoami()
        # console = 'console-sandbox' if self.environment == 'sandbox' else 'console'
        # target_url = 'https://%s.foodics.com/authorize?client_id=%s&state=%s' % (console, self.client_id, self.id)
        # return {
        #     'type': 'ir.actions.act_url',
        #     'target': 'self',
        #     'url': target_url,
        # }

    def foodic_import_data(self, url):
        access_token = self.access_token
        if access_token:
            access_token = access_token.strip()
            
        headers = {
            'Authorization': "Bearer %s" % access_token,
            'Accept': 'application/json',
        }
        _logger.info(f'Requesting {url}')
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            raise UserError(_("Connection Error: %s") % str(e))

        if response.status_code == 200:
            res = response.json()
            return res
        elif response.status_code == 401:
            raise UserError(_("Unauthorized! Please check your Access Token."))
        else:
            raise UserError(
                f'Something Went Wrong During Data Fetching from Foodics !\n HTTP Response Status Code is {response.status_code}')

    async def products_async_call(self, session, base_url, pg_no, **kwargs):
        while True:
            try:
                request_url = base_url + f"&page={pg_no}"
                print(f"Requesting {request_url}")
                _logger.info(f'Requesting {request_url}')
                async_response = await session.request('GET', url=request_url, raise_for_status=True, timeout=10,
                                                       **kwargs)
                assert int(async_response.headers['x-ratelimit-remaining']) > 10
                print(f"Received data for {request_url}")

                products_response_json = await async_response.json()

                self.env['product.template'].set_consumable_foodics_product_to_odoo(products_response_json)
                break
            except aiohttp.ClientError as c:

                _logger.error(c)
                _logger.info(f"Oops, the server connection was dropped on {request_url}. Retrying after 3 seconds")
                await asyncio.sleep(3)  # don't hammer the server
            except Exception as e:

                _logger.error(e)
                break

    async def invent_loc_async_call(self, session, base_url, pg_no, **kwargs):
        while True:
            try:
                request_url = base_url + f"?page={pg_no}"
                _logger.info(f"Requesting {request_url}")
                async_response = await session.request('GET', url=request_url, raise_for_status=True, timeout=10,
                                                       **kwargs)
                assert int(async_response.headers['x-ratelimit-remaining']) > 10
                _logger.info(f"Received data for {request_url}")

                invent_loc_response_json = await async_response.json()

                self.env['stock.location'].set_locations_to_odoo(invent_loc_response_json)
                break
            except aiohttp.ClientError as c:
                _logger.error(c)
                _logger.info(f"Oops, the server connection was dropped on {request_url}. Retrying after 3 seconds")
                await asyncio.sleep(3)  # don't hammer the server
            except Exception as e:

                _logger.error(e)
                break

    async def invent_count_async_call(self, session, base_url, pg_no, **kwargs):
        while True:
            try:
                request_url = base_url + f"&page={pg_no}"
                _logger.info(f"Requesting {request_url}")
                async_response = await session.request('GET', url=request_url, raise_for_status=True, timeout=10,
                                                       **kwargs)
                assert int(async_response.headers['x-ratelimit-remaining']) > 10
                _logger.info(f"Received data for {request_url}")

                invent_count_response_json = await async_response.json()
                self.env['stock.quant'].set_count_to_odoo(invent_count_response_json)
                break
            except aiohttp.ClientError as c:

                _logger.error(c)
                _logger.info(f"Oops, the server connection was dropped on {request_url}. Retrying after 3 seconds")
                await asyncio.sleep(3)  # don't hammer the server
            except Exception as e:

                _logger.error(e)
                break

    async def invent_trans_async_call(self, session, base_url, pg_no, **kwargs):
        while True:
            try:
                request_url = base_url + f"&page={pg_no}"
                _logger.info(f"Requesting {request_url}")
                async_response = await session.request('GET', url=request_url, raise_for_status=True, timeout=10,
                                                       **kwargs)
                assert int(async_response.headers['x-ratelimit-remaining']) > 10
                _logger.info(f"Received data for {request_url}")

                invent_trans_response_json = await async_response.json()
                self.env['stock.picking'].set_transaction_to_odoo(invent_trans_response_json)
                break
            except aiohttp.ClientError as c:

                _logger.error(c)
                _logger.info(f"Oops, the server connection was dropped on {request_url}. Retrying after 3 seconds")
                await asyncio.sleep(3)  # don't hammer the server
            except Exception as e:

                _logger.error(e)
                break

    def success_popup(self, data):
        return {
            "name": "Message",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "pop.message",
            "target": "new",
            "context": {
                "default_name": "Successfully %s Imported!" % data
            },
        }

    def get_branches(self):
        data_access_url = self.url + '/v5/branches'
        res = self.foodic_import_data(data_access_url)
        Branch = self.env['pos.config']
        Branch.set_branches_to_odoo(res)
        last_page = int(res.get('meta').get('last_page'))
        if last_page > 1:
            for page_no in range(int(res.get('meta').get('current_page')) + 1, last_page + 1):
                res = self.foodic_import_data(data_access_url + "?page={}".format(page_no))
                Branch.set_branches_to_odoo(res)
        return self.success_popup('Branches')

    def get_payment_methods(self):
        data_access_url = self.url + '/v5/payment_methods'
        res = self.foodic_import_data(data_access_url)
        PaymentMethods = self.env['pos.payment.method']
        PaymentMethods.set_payment_methods_to_odoo(res)
        last_page = int(res.get('meta').get('last_page'))
        if last_page > 1:
            for page_no in range(int(res.get('meta').get('current_page')) + 1, last_page + 1):
                res = self.foodic_import_data(data_access_url + "?page={}".format(page_no))
                PaymentMethods.set_payment_methods_to_odoo(res)
        return self.success_popup('Payment Methods')

    def get_categories_methods(self):
        data_access_url = self.url + '/v5/categories'
        res = self.foodic_import_data(data_access_url)
        PosCategory = self.env['pos.category']
        PosCategory.set_categories_to_odoo(res)
        last_page = int(res.get('meta').get('last_page'))
        if last_page > 1:
            for page_no in range(int(res.get('meta').get('current_page')) + 1, last_page + 1):
                res = self.foodic_import_data(data_access_url + "?page={}".format(page_no))
                PosCategory.set_categories_to_odoo(res)
        return self.success_popup('Categories')

    ##################################################################

    async def get_products_methods(self):
        try:
            access_token = self.access_token
            headers = {
                'authorization': "Bearer %s" % access_token,
                'content-type': 'text/plain',
            }
            data_access_url = self.url + '/v5/products?include=category,ingredients'
            sem = asyncio.Semaphore(1)
            async with sem:
                async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
                    req = await session.request('GET', url=data_access_url, raise_for_status=True)
                    res = await req.json()
                    # Note that this may raise an exception for non-2xx responses
                    # You can either handle that here, or pass the exception through
                    Product = self.env['product.template']
                    last_page = int(res['meta']['last_page'])
                    if last_page > 1:
                        for pg in range(int(res['meta']['current_page']) + 1, last_page + 1):
                            await asyncio.create_task(
                                self.products_async_call(session=session, base_url=data_access_url, pg_no=pg))
                            await asyncio.sleep(2.5)

                        print('finished products')

                    self.env['product.template'].set_consumable_foodics_product_to_odoo(res)
                    return self.success_popup('Products')
        except Exception as e:
            _logger.error(e)
            raise UserError((
                                f"Something went wrong while fetching consumable products from Foodics server!\nPlease try again later\nHere's the technical details of what happened:\n{e}"))

    #########################################################
    async def get_invent_count_methods(self, from_date='', before_date=''):

        try:

            access_token = self.access_token
            headers = {
                'authorization': "Bearer %s" % access_token,
                'content-type': 'text/plain',
            }
            data_access_url = self.url + f'/v5/inventory_counts?include=branch,items&filter[status]=2&filter[business_date_before]={before_date}&filter[business_date_after]={from_date}'
            sem = asyncio.Semaphore(1)
            async with sem:
                async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
                    InventAdjust = self.env['stock.quant']
                    _logger.info(f"Requesting {data_access_url}")

                    req = await session.request('GET', url=data_access_url, raise_for_status=True)
                    res = await req.json()
                    _logger.info(f"Received data for {data_access_url}")
                    InventAdjust.set_count_to_odoo(res)
                    # Note that this may raise an exception for non-2xx responses
                    # You can either handle that here, or pass the exception through
                    _logger.info('first step done')
                    last_page = int(res['meta']['last_page'])
                    if last_page > 1:

                        for pg in range((int(res['meta']['current_page']) + 1), (last_page + 1)):
                            # fetching_tasks.append((await session.request('GET', url=data_access_url, raise_for_status=True)))
                            await asyncio.create_task(
                                self.invent_count_async_call(session=session, base_url=data_access_url, pg_no=pg))
                            await asyncio.sleep(2.5)

                        _logger.info('finished inventory counts')

                    return self.success_popup('Transactions')
        except Exception as e:
            _logger.error(e)
            raise UserError((f"Something went wrong while fetching inventory counts from Foodics server!\nPlease try again later\nHere's the available technical details of what happened:\n{e}"))

    async def get_invent_locations_methods(self):

        try:
            access_token = self.access_token
            headers = {
                'authorization': "Bearer %s" % access_token,
                'content-type': 'text/plain',
            }
            wh_access_url = self.url + '/v5/warehouses'
            br_access_url = self.url + '/v5/branches'
            sem = asyncio.Semaphore(1)
            async with sem:
                async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
                    wh_req = await session.request('GET', url=wh_access_url, raise_for_status=True)
                    wh_res = await wh_req.json()
                    await asyncio.sleep(1)
                    br_req = await session.request('GET', url=br_access_url, raise_for_status=True)
                    br_res = await br_req.json()
                    # Note that this may raise an exception for non-2xx responses
                    # You can either handle that here, or pass the exception through
                    InventLocation = self.env['stock.location']
                    wh_last_page = int(wh_res['meta']['last_page'])
                    br_last_page = int(br_res['meta']['last_page'])
                    if wh_last_page > 1:

                        for pg in range((int(wh_res['meta']['current_page']) + 1), (wh_last_page + 1)):
                            await asyncio.create_task(
                                self.invent_loc_async_call(session=session, base_url=wh_access_url, pg_no=pg))
                            await asyncio.sleep(2.5)
                    if br_last_page > 1:

                        for pg in range((int(br_res['meta']['current_page']) + 1), (br_last_page + 1)):
                            await asyncio.create_task(
                                self.invent_loc_async_call(session=session, base_url=br_access_url, pg_no=pg))
                            await asyncio.sleep(2.5)
                    _logger.info('finished inventory locations')

                    InventLocation.set_locations_to_odoo(wh_res)
                    InventLocation.set_locations_to_odoo(br_res)
                    return self.success_popup('Products')
        except Exception as e:
            _logger.error(e)
            raise UserError((
                                f"Something went wrong while fetching inventory locations from Foodics server!\nPlease try again later\nHere's the available technical details of what happened:\n{e}"))

    async def get_invent_transactions_methods(self, from_date='', before_date=''):

        try:
            access_token = self.access_token
            headers = {
                'authorization': "Bearer %s" % access_token,
                'content-type': 'text/plain',
            }
            data_access_url = self.url + f'/v5/inventory_transactions?include=branch,other_branch,other_transaction,items&filter[status]=1,2,3,4&filter[type]=2,11&filter[business_date_after]={from_date}&filter[business_date_before]={before_date}'
            sem = asyncio.Semaphore(1)
            async with sem:
                async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
                    InventTransfer = self.env['stock.picking']
                    _logger.info(f"Requesting {data_access_url}")

                    req = await session.request('GET', url=data_access_url, raise_for_status=True)
                    res = await req.json()
                    _logger.info(f"Received data for {data_access_url}")
                    InventTransfer.set_transaction_to_odoo(res)
                    # Note that this may raise an exception for non-2xx responses
                    # You can either handle that here, or pass the exception through
                    _logger.info('first step done')
                    last_page = int(res['meta']['last_page'])
                    if last_page > 1:

                        for pg in range((int(res['meta']['current_page']) + 1), (last_page + 1)):
                            # fetching_tasks.append((await session.request('GET', url=data_access_url, raise_for_status=True)))
                            await asyncio.create_task(
                                self.invent_trans_async_call(session=session, base_url=data_access_url, pg_no=pg))
                            await asyncio.sleep(2.5)

                        _logger.info('finished inventory transfers')

                    return self.success_popup('Transactions')
        except Exception as e:
            _logger.error(e)
            raise UserError((
                                f"Something went wrong while importing inventory transactions from Foodics server!\nPlease try again later\nHere's the available technical details of what happened:\n{e}"))

    def foodics_import_purchase_orders(self, from_date='', before_date=''):
        try:

            data_access_url = self.url + f'/v5/purchase_orders?include=supplier,items,branch&filter[business_date_after]={from_date}&filter[business_date_before]={before_date}'
            res = self.foodic_import_data(data_access_url)
            purchase_order = self.env['purchase.order']
            purchase_order.set_analytic_accounts_to_odoo(res)
            purchase_order.set_orders_to_odoo(res)
            last_page = int(res.get('meta').get('last_page'))
            if last_page > 1:
                for page_no in range(int(res.get('meta').get('current_page')) + 1, last_page + 1):
                    res = self.foodic_import_data(data_access_url + "&page={}".format(page_no))
                    purchase_order.set_analytic_accounts_to_odoo(res)
                    purchase_order.set_orders_to_odoo(res)
        except Exception as e:
            _logger.error(e)
            raise UserError((
                                f"Something went wrong while fetching purchase orders from Foodics server!\nPlease try again later\nHere's the available technical details of what happened:\n{e}"))

    def get_orders_methods(self, from_date='', before_date=''):
        try:

            self.from_date = from_date
            to_date = (datetime.datetime.now().date() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            url = self.url + "/v5/orders?include=branch,charges,customer,products.product,payments,payments.paymentMethod,products.taxes,creator,products.options.modifierOption&page={}&filter[business_date_after]={}&filter[business_date_before]={}"
            res = self.foodic_import_data(url.format(self.page, from_date, before_date))
            Order = self.env['pos.order']
            Order.set_orders_to_odoo(res, to_date)
            if res and res.get('meta', {}):
                last_page = int(res.get('meta').get('last_page'))
                current_page = int(res.get('meta').get('current_page'))
                if last_page > 1:
                    for page_no in range(current_page + 1, last_page + 1):
                        if page_no % 30 == 0:
                            time.sleep(60)
                        res = self.foodic_import_data(url.format(page_no, from_date, before_date))
                        self.page = page_no
                        Order.set_orders_to_odoo(res, to_date)
                    self.page = 1
                    self.from_date = (datetime.datetime.now().date() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                return self.success_popup('Orders')
        except Exception as e:
            _logger.error(e)
            raise UserError((
                                f"Something went wrong while fetching POS orders from Foodics server!\nPlease try again later\nHere's the available technical details of what happened:\n{e}"))

    def cron_sync_pos_order(self):
        for connector in self.search([('state', '=', 'authenticated')]):
            connector.get_orders_methods(((datetime.datetime.now() - relativedelta(days=2)).date().strftime('%Y-%m-%d')), ((datetime.datetime.now()).date().strftime('%Y-%m-%d')))
