from odoo import models, fields, api
import requests


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_weather_score = fields.Integer(string='Weather Score', help='Calculated score based on weather at lead location')
    x_temperature = fields.Float(string='Temperature (°C)', digits=(16, 2), help='Temperature at the lead\'s location')

    def _get_openweather_api_key(self) :
        """Fetch OpenWeather API key from system parameters.
        Set it in Settings > Technical > System Parameters with key:
        'weather_lead_scoring.openweather_api_key'
        """
        key = self.env['ir.config_parameter'].sudo().get_param('weather_lead_scoring.openweather_api_key')
        return key or ''

    def _build_openweather_query(self):
        self.ensure_one()
        # Prefer explicit city/country on the lead; fallback to partner
        city = (self.city or self.partner_id.city or '').strip()
        # Use country code if available, else country name
        country_code = (self.country_id and self.country_id.code) or (self.partner_id.country_id and self.partner_id.country_id.code) or ''
        country_name = (self.country_id and self.country_id.name) or (self.partner_id.country_id and self.partner_id.country_id.name) or ''
        country = (country_code or country_name or '').strip()
        # Compose q param as "city,country"
        if city and country:
            return f"{city},{country}"
        return city or country or ''

    def _compute_weather_score_from_condition(self, condition, temperature_c) :
        cond = (condition or '').strip().lower()
        if cond == 'clear':
            score = 100
        elif cond in ('clouds', 'drizzle'):
            score = 50
        elif cond in ('rain', 'thunderstorm', 'snow'):
            score = 10
        else:
            score = 20
        if temperature_c is not None and temperature_c > 25.0:
            score += 20
        return score

    def action_update_weather_score(self):
        for lead in self:
            # Default on error
            def _fail(msg):
                lead.sudo().write({'x_weather_score': 0, 'x_temperature': 0.0})
                try:
                    lead.message_post(body=f"Weather scoring failed: {msg}")
                except Exception:
                    pass

            api_key = lead._get_openweather_api_key()
            if not api_key:
                _fail('OpenWeather API key is missing. Configure system parameter "weather_lead_scoring.openweather_api_key".')
                continue

            query = lead._build_openweather_query()
            if not query:
                _fail('Lead has no city/country information to query weather.')
                continue

            url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': query,
                'appid': api_key,
                'units': 'metric',  # get °C directly
            }
            try:
                resp = requests.get(url, params=params, timeout=15)
            except Exception as e:
                _fail(f'Network error: {e}')
                continue

            if resp.status_code != 200:
                try:
                    data = resp.json()
                    err_msg = data.get('message') or resp.text
                except Exception:
                    err_msg = resp.text
                _fail(f'HTTP {resp.status_code}: {err_msg}')
                continue

            try:
                payload = resp.json()
                temp_c = float(payload.get('main', {}).get('temp'))
                condition = (payload.get('weather') or [{}])[0].get('main') or ''
            except Exception as e:
                _fail(f'Parse error: {e}')
                continue

            score = lead._compute_weather_score_from_condition(condition, temp_c)
            lead.sudo().write({
                'x_weather_score': int(score),
                'x_temperature': temp_c,
            })
            # Optional: log success
            try:
                lead.message_post(body=f"Weather updated: {condition or 'N/A'}; {temp_c} °C; score = {score}")
            except Exception:
                pass 