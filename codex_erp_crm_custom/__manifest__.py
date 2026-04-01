{
    'name': 'CRM Social & Industry Fields',
    'version': '18.0.1.0.0',
    'category': 'CRM',
    'summary': 'Adds Industry Type and Social Media fields (Facebook, Instagram, LinkedIn, TikTok) to CRM Leads/Opportunities',
    'description': """
CRM Social & Industry Fields
============================
This module adds additional fields to the CRM Lead/Opportunity form:
- Industry Type  
- Facebook URL  
- Instagram URL  
- LinkedIn URL  
- TikTok URL  

All social fields use URL widgets with helpful placeholders and appear right after the Website field.
""",
    'author': 'Usama Wazir',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_inherit_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
