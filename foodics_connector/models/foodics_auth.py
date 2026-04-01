# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class FoodicsAuth(models.AbstractModel):
    _name = 'foodics.auth'
    _description = 'Foodics Authorization'
    

    @api.model
    def exchange_code_for_token(self, user, code):
        """
        Exchange authorization code for access and refresh tokens.
        """
        # Get Client ID and Secret from Config Settings
        params = self.env['ir.config_parameter'].sudo()
        client_id = params.get_param('foodics_connector.foodics_client_id')
        client_secret = params.get_param('foodics_connector.foodics_client_secret')
        redirect_uri_override = params.get_param('foodics_connector.foodics_redirect_uri')
        redirect_uri = redirect_uri_override or (params.get_param('web.base.url') + '/web/login')

        if not client_id or not client_secret:
            raise UserError(_("Foodics Client ID and Client Secret are not configured in Settings."))

        env_type = params.get_param('foodics_connector.foodics_environment')
        
        if env_type == 'production':
            url = "https://api.foodics.com/oauth/token"
        else:
            url = "https://api-sandbox.foodics.com/oauth/token"
        
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }
        
        _logger.info("Foodics OAuth: Exchanging code with payload (redirect_uri=%s)", redirect_uri)

        try:
            response = requests.post(url, json=payload)
            _logger.info("Foodics OAuth: Response Status: %s", response.status_code)
            _logger.info("Foodics OAuth: Response Content: %s", response.text)
            
            response.raise_for_status()
            data = response.json()
            
            # Create or Update Token Record
            auth_rec = self.env["foodics.connector"].create({
                'access_token': data.get('access_token'),
                'environment': env_type,
            })

            auth_rec.authenticate()
            #  Delete old records except the new one
            old_records = self.env['foodics.connector'].search([('id', '!=', auth_rec.id)])
            if old_records:
                old_records.unlink()
            return True
        except requests.exceptions.RequestException as e:
            _logger.error("Foodics Token Exchange Failed: %s", e)
            return False

    @api.model
    def get_authorization_url(self):
        """
        Generate Foodics Authorization URL.
        """
        params = self.env['ir.config_parameter'].sudo()
        client_id = params.get_param('foodics_connector.foodics_client_id')
        env_type = params.get_param('foodics_connector.foodics_environment')
        
        if not client_id:
            return False
            
        if env_type == 'production':
            base_url = "https://console.foodics.com/authorize"
        else:
            base_url = "https://console-sandbox.foodics.com/authorize"
            

        # Using simple format: ?client_id=...&state=...
        
        return f"{base_url}?client_id={client_id}&state=AutoRedirect"
