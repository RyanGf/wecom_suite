# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WeComAppCategory(models.Model):
    """
    WeChat Work Application Category Model
    This model represents categories for WeChat Work applications, supporting a hierarchical structure.
    """
    _name = "wecom.app.category"
    _description = "WeChat Work Application Category"
    _inherit = ['wecom.base']
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'parent_path'

    name = fields.Char(required=True, translate=True, help="Category name")
    complete_name = fields.Char(compute='_compute_complete_name', store=True, help="Full category name including parents")
    parent_id = fields.Many2one('wecom.app.category', string='Parent Category', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('wecom.app.category', 'parent_id', string='Child Categories')
    sequence = fields.Integer(default=10, help="Sequence for ordering")

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Compute the complete name of the category"""
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        """Check that there's no recursive categories"""
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))

    @api.model
    def name_create(self, name):
        """Allow quick creation of categories"""
        return self.create({'name': name}).name_get()[0]