{
    'name': 'Partner Sales & Accounting Privacy',
    'version': '1.0',
    'summary': (
        "Enhances contact privacy by dynamically controlling the visibility of "
        "Sales and Accounting tabs and menus based on user roles. "
        "Users without the respective access groups cannot see the Sales or Accounting tabs, "
        "and the Accounting menus  are hidden to prevent access errors, "
        "while still allowing access to customer details."
    ),
    'category': 'Contacts',
    'author': '',
    'depends': ['base', 'contacts', 'account',],
    'data': [
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
