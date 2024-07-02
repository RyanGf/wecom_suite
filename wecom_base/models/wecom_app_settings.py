# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import json

class WeComAppSettings(models.Model):
    """
    WeChat Work Application Settings Model
    This model stores settings for WeChat Work applications.
    """
    _name = "wecom.app.settings"
    _description = "WeChat Work Application Settings"
    _inherit = ['wecom.base']

    app_id = fields.Many2one('wecom.application', required=True, ondelete='cascade', help="Related application")
    key = fields.Char(required=True, help="Setting key")
    value = fields.Text(required=True, help="Setting value")
    value_type = fields.Selection([
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON')
    ], default='string', required=True, help="Type of the setting value")

    _sql_constraints = [
        ('app_key_uniq', 'unique (app_id, key)', _("Settings key must be unique per application!"))
    ]

    @api.model
    def create(self, vals):
        """Override create to convert value based on value_type"""
        vals = self._convert_value(vals)
        return super(WeComAppSettings, self).create(vals)

    def write(self, vals):
        """Override write to convert value based on value_type"""
        vals = self._convert_value(vals)
        return super(WeComAppSettings, self).write(vals)

    def _convert_value(self, vals):
        """Convert value based on value_type"""
        if 'value' in vals and 'value_type' in vals:
            if vals['value_type'] == 'integer':
                vals['value'] = int(vals['value'])
            elif vals['value_type'] == 'float':
                vals['value'] = float(vals['value'])
            elif vals['value_type'] == 'boolean':
                vals['value'] = bool(vals['value'])
            elif vals['value_type'] == 'json':
                try:
                    json.loads(vals['value'])  # Validate JSON
                except json.JSONDecodeError:
                    raise ValueError(_("Invalid JSON format"))
        return vals

    def get_value(self):
        """Get the converted value based on value_type"""
        self.ensure_one()
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            return json.loads(self.value)
        return self.value