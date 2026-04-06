# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models

class FieldSelection(models.Model):
    _name = 'sh.model.fields.selection'
    _description = "Fields Selection"
    sh_field_id = fields.Many2one(
        'sh.custom.model.task', string="SH Custom Task")
    value = fields.Char(required=True)
    name = fields.Char(translate=True, required=True)
    sequence = fields.Integer(default=1000)
