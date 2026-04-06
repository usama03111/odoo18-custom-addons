{
    'name': 'Material Request',
    'version': '1.0',
    'summary': 'Material Requests & Project Cost Tracking',
    'description': 'Allows site engineers to request materials with approval workflow. Integrates with Projects to track requests and calculate real time Material Costs from generated RFQs.',
    'author': 'Usama Wazir',
    'category': 'Construction',
    'depends': ['base', 'project', 'product', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/material_request_views.xml',
        'views/project_project_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
