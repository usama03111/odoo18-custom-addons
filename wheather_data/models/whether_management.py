import requests

from odoo import models, fields , api
import meteomatics.api as meteomatics_api
import  datetime as dt
import logging
_logger = logging.getLogger(__name__)

class WeatherData(models.Model):

    _name = 'weather.data'
    _description = 'Weather Data'

    name = fields.Char(string="Location")
    temperature = fields.Char(string="Temperature")
    condition = fields.Char(string="Condition")

    def fetch_and_store_weather_data(self):
        # weather_data = self._fetch_weather_data()
        # if weather_data:
        #     if self:
        #         # If editing an existing record, update it
        #         self.write({
        #             'name': weather_data['location'],
        #             'temperature': weather_data['temperature'],
        #             'condition': weather_data['condition']
        #         })
        #     else:
        #         # Otherwise, create a new one
        #         self.create({
        #             'name': weather_data['location'],
        #             'temperature': weather_data['temperature'],
        #             'condition': weather_data['condition']
        #         })
        channel = self.env['discuss.channel'].browse([52,54])
        # channel = self.env['discuss.channel'].search([50])
        if channel:
            channel.unlink()
            print(channel)

    def _fetch_weather_data(self):
        # Meteomatics API credentials
        username = 'self_wazir_usama'
        password = '0Te1gRSwJqfxM90o51Oc'

        coordinates = [(51.5073219, -0.1276474)]  # London coordinates
        parameters = ['t_2m:C']  # Temperature at 2 meters
        model = 'mix'

        # Set start and end date for the request
        startdate = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        enddate = startdate + dt.timedelta(hours=1)  # Forecast for the next hour
        interval = dt.timedelta(hours=1)

        try:
            # Query the time series from Meteomatics
            df = meteomatics_api.query_time_series(coordinates, startdate, enddate, interval, parameters, username,
                                                   password, model=model)

            # Log the entire response to check its structure
            print(f"API response: {df}")

            # Parse the temperature value from the DataFrame
            temperature = df['t_2m:C'].iloc[0]  # Correct way to access column data by column name and row index

            # Log the extracted temperature to verify it's correct
            print(f"Extracted temperature: {temperature}")

            return {
                'temperature': temperature,
                'location': 'London',
                'condition': 'Clear'  # Default to 'Clear'
            }

        except Exception as e:
            _logger.error(f"Error fetching weather data: {str(e)}")
            return None



    def test_connection(self):
        url = "https://ihejtn-rq.myshopify.com/admin/api/2025-07/products.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": "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"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Shopify API Error: {response.status_code} - {response.text}")

        products = response.json().get("products", [])

        for shopify_product in products:
            for variant in shopify_product.get("variants", []):
                name = f"{shopify_product['title']} - {variant['title']}"
                qty = variant.get("inventory_quantity") or 0
                sku = variant.get("sku") or f"shopify_{variant['id']}"
                price = float(variant.get("price") or 0)



                # Search existing product in Odoo by SKU
                odoo_product = self.env["product.product"].search([("default_code", "=", sku)], limit=1)
                if odoo_product:
                    odoo_product.write({
                        "name": name,
                        "list_price": price
                    })
                template = self.env["product.template"].create({
                    "name": shopify_product["title"],
                    "type": "consu"
                })

                # for variant in shopify_product["variants"]:
                self.env["product.product"].create({
                    "product_tmpl_id": template.id,
                    "default_code": sku,
                    "lst_price": price,
                    "name": f"{shopify_product['title']} - {variant['title']}"
                })
