# Weather Lead Scoring

Weather-based lead scoring for Odoo CRM. Adds two fields to `crm.lead` and a button/server action to fetch the current weather via OpenWeather and compute a score.

## Features
- Fields on `crm.lead`:
  - `x_weather_score` (Integer)
  - `x_temperature` (Float, °C)
- Settings (CRM app): enter your OpenWeather API key.
- Server Action bound to `crm.lead`: "Update Weather Score" (available from the Action menu).
- Robust error handling: on failure, sets fields to 0 and posts a message to the lead chatter.

## Install
1. Copy `weather_lead_scoring` into your addons path.
2. Update app list and install via Apps, or restart Odoo with:
   - `-u weather_lead_scoring`
3. Configure API key:
   - Settings → CRM → Weather Lead Scoring → OpenWeather API Key
   - System Parameter used: `weather_lead_scoring.openweather_api_key`

## Usage
1. Open a lead with City and Country set (or a linked partner with these fields).
2. Use Action → "Update Weather Score" from the Action menu.
3. Score and temperature populate; a chatter message logs the result or the error reason.

## Scoring Rules
- Clear → 100
- Clouds/Drizzle → 50
- Rain/Thunderstorm/Snow → 10
- Others → 20
- Bonus: +20 if temperature > 25°C

## Assumptions
- City and Country (or partner equivalents) are enough for OpenWeather `q` param.
- Temperature is in metric units (°C).

## Design Notes
- API key stored as an Odoo system parameter and editable on `res.config.settings`.
- Logic implemented on `crm.lead` method `action_update_weather_score` to keep concerns close to the data model.
- Server Action created and bound to `crm.lead` for convenient manual triggering without extra UI changes.
- Errors handled gracefully: fields reset to 0, human-readable chatter message posted. 