# -*- coding: utf-8 -*-
{
    'name': 'RMA Management',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'sequence': 25,
    'summary': 'Complete Return Merchandise Authorization (RMA) Management System',
    'description': """
RMA Management System
=====================

A comprehensive Return Merchandise Authorization (RMA) management system that provides:

**Core Features:**
* Complete RMA workflow (Draft → Submitted → Approved → Received → Inspected → Resolved)
* Multi-line RMA requests with product details
* Integration with Sale Orders and Products
* Customer portal integration ready
* Email notifications and tracking
* Advanced search and filtering capabilities

**Workflow Management:**
* Status tracking with visual indicators
* Approval workflow with manager permissions
* Resolution types: Refund, Replace, Repair, Credit Note, Exchange
* Return shipping management with carrier and tracking support

**Analytics & Reporting:**
* Group by Customer, Reason, Status, Priority, Resolution Type
* Pivot tables and graphs for RMA analysis
* Calendar view for scheduling
* Kanban boards for visual workflow management

**Global Compatibility:**
* Multi-currency support
* Multi-company support
* Configurable reasons and tags
* Flexible address formatting
* Supports international shipping carriers

**Integration Features:**
* Sale Order integration with RMA buttons
* Product template integration with RMA statistics
* Customer integration with RMA history
* Chatter integration for communication
* Activity tracking and notifications

**Portal Ready:**
* Backend designed for portal extension
* Customer-facing RMA request creation
* Status tracking for customers
* Document upload capabilities (ready for portal extension)

This module provides a solid foundation for managing product returns efficiently
while maintaining full traceability and customer satisfaction.
    """,
    'author': 'Irfan Ullah',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'stock',
        'mail',
        'hr',
        'hr_skills',
        'delivery',  # For shipping carrier integration
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'security/employee_custom_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        # 'security/rma_security.xml',

        # Data
        # 'data/rma_sequence.xml',
        # 'data/rma_reasons.xml',
        # 'data/email_templates.xml',

        # Views
        'views/rma_request_views.xml',
        'views/stock_inherit.xml',
        'views/hr_employee_inherit.xml',
        # 'views/rma_reason_views.xml',
        # 'views/rma_tag_views.xml',
        # 'views/sale_order_views.xml',
        # 'views/product_views.xml',
        # 'views/partner_views.xml',
        # 'views/rma_menus.xml',

        # Reports (if needed)
        # 'reports/rma_report_views.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 500.00,
    'currency': 'USD',
    'support': 'support@yourcompany.com',
    'maintainers': ['Irfan Ullah'],
}