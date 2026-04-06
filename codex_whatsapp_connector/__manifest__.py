{
    "name": "Codex Whatsapp Connector",
    "version": "1.0",
    "summary": "Adds a 'Send in WhatsApp' button in the chatter composer and Discuss channels",
    "Author": "Usama Wazir",
    "Company": "Codex",
    "depends": ["mail", "crm","base", "web"],
    "external_dependencies": {
        "python": ["requests"]
    },
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/whatsapp_account_views.xml',
        'views/whatsapp_template_views.xml',
        'views/whatsapp_menus.xml',
        'views/ir_actions_server_views.xml',
        'views/res_config_settings_views.xml',],
    "assets": {
        "web.assets_backend": [
            "codex_whatsapp_connector/static/src/js/whatsapp_button_visibility.js",
            "codex_whatsapp_connector/static/src/js/message_with_button.js",
            "codex_whatsapp_connector/static/src/xml/message_with_button.xml",
            "codex_whatsapp_connector/static/src/xml/whatsapp_chatter_button.xml",
            "codex_whatsapp_connector/static/src/xml/whatsapp_sidebar.xml",
            "codex_whatsapp_connector/static/src/js/whatsapp_sidebar.js",
            "codex_whatsapp_connector/static/src/css/whatsapp_sidebar.css",
        ],

    },
    "installable": True,
    "application": False,
    "license": "LGPL-3"
}
