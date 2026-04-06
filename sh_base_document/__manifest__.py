# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    "name": "Base Document Management",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Account Document Management Invoice Document Management Bill Document Management Credit Note Document Management Debit Note Document Management Invoices Documents Management Bills Documents Management Credit Notes Documents Management Debit Notes Documents Management Customer Document Management Customers Documents Management Sales Document Management Sales Order Document Management Sale Order Document Management Quotation Document Management Sales Documents Management Sales Orders Documents Management Sale Orders Documents Management Quotation Documents Management Purchase Document Management Purchase Order Document Management Request For Quotation Document Management RFQ Document Management Purchase Documents Management Purchase Orders Documents Management Requests For Quotations Documents Management RFQ Documents Management Employee Document Management Employees Document Management Contact Document Management Contacts Documents Management Project Document Management Projects Documents Management Project Task Document Management Projects Tasks Documents Management Odoo Manage Document In Odoo Manage Document Odoo",
    "description": """"Base Document Management" is the base module for the document management modules.""",
    "version": "0.0.1",
    'depends': ['base_setup', 'web','mail'],
    'data': [
            'security/base_document_security.xml',
            'security/ir.model.access.csv',
            'views/sh_ir_attachments_views.xml',
            'views/sh_tags.xml',
            ],
    'images': ['static/description/background.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    }
