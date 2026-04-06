{
    'name': 'Sale Sub Customer',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Add Sub Customer in Sale Order and Invoice with checkbox control',
    'author': 'Aftab Khan',
    'depends': ['sale', 'account'],
    'data': [
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
