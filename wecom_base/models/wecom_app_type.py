# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class WeComAppType(models.Model):
    """
    WeChat Work Application Type Model
    This model represents different types of WeChat Work applications.
    """
    _name = "wecom.app.type"
    _description = "WeChat Work Application Type"
    _inherit = ['wecom.base']
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True, help="Name of the application type")
    code = fields.Char(required=True, help="Unique code for the application type")
    sequence = fields.Integer(default=10, help="Sequence for ordering")
    description = fields.Text(translate=True, help="Description of the application type")

    _sql_constraints = [
        ("code_uniq", "unique (code)", _("The type code must be unique!"))
    ]

    @api.model
    def create(self, vals):
        """Override create to ensure code is uppercase"""
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        return super(WeComAppType, self).create(vals)

    def write(self, vals):
        """Override write to ensure code is uppercase"""
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        return super(WeComAppType, self).write(vals)

    def name_get(self):
        """Custom name_get to include code"""
        return [(record.id, f"[{record.code}] {record.name}") for record in self]