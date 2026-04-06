{
    'name': 'Survey Image Extension',
    'version': '1.0',
    'category': 'Marketing/Surveys',
    'summary': 'Adds image support to survey multiple-choice questions in the portal',
    'description': """
        Survey Image Extension
        =====================
        
        This module extends the Odoo Survey module to add image support for multiple-choice questions.
        
        Features:
        - Add image field to survey question suggested answers
        - Display images in portal for multiple-choice questions
        - Inherit survey templates to show images alongside text options
    """,
    'depends': ['survey'],
    'data': [
        'views/survey_userinput_line.xml',
        'views/survey_templates.xml',
    ],
    'assets': {
    'web.assets_frontend': [
        'survey_image_extension/static/src/survey_attachment.js',
        'survey_image_extension/static/src/survey_attachment_adv.js',
        'survey_image_extension/static/src/survey_attachement_error.js',
    ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
