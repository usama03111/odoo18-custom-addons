{
    'name': 'Transport Logistics',
    'version': '18.0.1.0.0',
    'category': 'Services/Logistics',
    'summary': 'Manage Transport & Cargo Operations',
    'description': """
        Transport Logistics Management System
        =====================================
        Manage Consignment Notes (Builty), Vehicle Loading, and Delivery Operations.
        Designed for manual/paper-based logistics companies moving to Odoo.
    """,
    'author': 'Usama Wazir',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/transport_builty_views.xml',
        'views/transport_batch_views.xml',
        'views/transport_city_views.xml',
    ],


    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
