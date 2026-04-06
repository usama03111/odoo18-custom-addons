{
    'name': 'Transport Booking Fast',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'High-speed transport booking interface',
    'description': """ A  transport booking system built with OWL.""",
    'depends': ['base', 'web'],

    'data': [
    'security/ir.model.access.csv',
    # LOAD VIEWS & ACTIONS
    'views/transport_route_views.xml',
    'views/transport_vehicle_views.xml',
    'views/transport_booking_data.xml',
    # LOAD MENUS
    'views/transport_booking_menus.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'transport_booking_fast/static/src/js/**/*',
            'transport_booking_fast/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
