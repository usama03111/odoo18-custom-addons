from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    industry_type = fields.Char(string="Industry Type")
    facebook = fields.Char(string="Facebook URL")
    instagram = fields.Char(string="Instagram URL")
    linkedin = fields.Char(string="LinkedIn URL")
    tiktok = fields.Char(string="TikTok URL")
