{
    'name': 'POS Loyalty Discount',
    'version': '1.0',
    'summary': 'Automatic POS Discounts based on Loyalty Score',
    'description': 'Automatically applies 5% or 10% discount in POS based on customer loyalty score.',
    'author': 'Usama Wazir',
    'category': 'Sales/Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale.assets_prod': [
            'pos_loyalty_discount/static/src/js/pos_loyalty.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
