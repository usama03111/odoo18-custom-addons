from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    openweather_api_key = fields.Char(
        string='OpenWeather API Key',
        config_parameter='weather_lead_scoring.openweather_api_key',
        help='API key for OpenWeather. Used to fetch current weather for leads.'
    )
