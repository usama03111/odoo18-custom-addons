# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    foodics_client_id = fields.Char(string='Foodics Client ID', config_parameter='foodics_connector.foodics_client_id')
    foodics_client_secret = fields.Char(string='Foodics Client Secret', config_parameter='foodics_connector.foodics_client_secret')
    foodics_environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('production', 'Production')
    ], string='Environment', default='sandbox', config_parameter='foodics_connector.foodics_environment')
    foodics_redirect_uri = fields.Char(string='Redirect URI Override', config_parameter='foodics_connector.foodics_redirect_uri', help="Leave empty to use the system default")
