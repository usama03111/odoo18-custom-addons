# -*- coding: utf-8 -*-
{
    'name': 'Weather Lead Scoring',
    'version': '1.0.0',
    'Author': 'Usama Wazir',
    'summary': 'Enhance CRM leads with real-time weather data and automated scoring',
    'description': """
Weather Lead Scoring Module

This module integrates Odoo CRM with the OpenWeather API to fetch real-time weather data
based on the lead's location and automatically calculate a weather-based score.

Key Features:
- Fetches live temperature and weather conditions using OpenWeather API
- Automatically calculates a weather score for each lead
- Stores temperature (°C) and weather score on CRM leads
- Smart scoring logic based on weather conditions (Clear, Clouds, Rain, etc.)
- Additional scoring boost for higher temperatures
- Configurable API key via system parameters
- Error handling with chatter logging for better traceability

Configuration:
- Go to Settings > Technical > System Parameters
- Add key: weather_lead_scoring.openweather_api_key

Use Case:
This module helps sales teams prioritize leads based on environmental conditions,
making it especially useful for weather-sensitive businesses.

Technical Notes:
- Extends crm.lead model
- Uses external API integration with proper error handling
- Supports both lead and partner location fallback
    """,
    'category': 'Sales/CRM',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
        'views/res_config_settings_views.xml',
        'views/server_actions.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}