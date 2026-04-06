{
    'name': 'Purchase Order Date',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'Purchase Order Date',
    'description': """
        Customizes the Purchase To Show The Creation Date
    """,
    'depends': ['purchase',],
    'data': [
        'views/purchase_order_date_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
