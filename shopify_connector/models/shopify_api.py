import requests
from odoo import models

class ShopifyAPI(models.Model):
    _name = 'shopify.api'
    _description = 'Shopify API Test'

    def test_connection(self):
        url = "https://mystore.myshopify.com/admin/api/2025-01/shop.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": "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"
        }
        response = requests.get(url, headers=headers)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.json())
