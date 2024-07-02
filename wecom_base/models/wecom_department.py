# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class WeComDepartment(models.Model):
    _name = 'wecom.department'
    _description = 'WeChat Work Department'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'name'
    _order = 'parent_path'

    name = fields.Char(string='Department Name', required=True, translate=True)
    wecom_id = fields.Integer(string='WeChat Work Department ID', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    parent_id = fields.Many2one('wecom.department', string='Parent Department', index=True, ondelete='cascade')
    child_ids = fields.One2many('wecom.department', 'parent_id', string='Child Departments')
    parent_path = fields.Char(index=True)

    active = fields.Boolean(default=True, string='Active')
    wecom_order = fields.Integer(string='WeChat Work Order', default=0)

    member_count = fields.Integer(string='Member Count', compute='_compute_member_count', store=True)

    odoo_department_id = fields.Many2one('hr.department', string='Odoo Department')

    _sql_constraints = [
        ('wecom_id_company_uniq', 'unique(wecom_id, company_id)',
         'WeChat Work Department ID must be unique per company!')
    ]

    @api.depends('child_ids', 'child_ids.member_count')
    def _compute_member_count(self):
        for department in self:
            department.member_count = len(department.mapped('child_ids.member_count'))

    @api.model
    def sync_departments(self):
        api_service = self.env['wecom.api.service']
        company = self.env.company

        try:
            response = api_service.call_api(company.id, 'department/list', method='GET')
            if response.get('errcode') == 0:
                departments = response.get('department', [])
                self._process_departments(departments)
                return True
            else:
                raise UserError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
                    'code': response.get('errcode'),
                    'msg': response.get('errmsg')
                })
        except Exception as e:
            _logger.error(f"Failed to sync WeChat Work departments: {str(e)}")
            raise UserError(_("Failed to sync departments: %s") % str(e))

    def _process_departments(self, departments):
        for dept_data in departments:
            existing_dept = self.search([('wecom_id', '=', dept_data['id']), ('company_id', '=', self.env.company.id)])
            vals = {
                'name': dept_data['name'],
                'wecom_id': dept_data['id'],
                'company_id': self.env.company.id,
                'parent_id': self.search(
                    [('wecom_id', '=', dept_data.get('parentid')), ('company_id', '=', self.env.company.id)]).id,
                'wecom_order': dept_data.get('order', 0),
            }
            if existing_dept:
                existing_dept.write(vals)
            else:
                self.create(vals)

    def action_sync_to_odoo(self):
        self.ensure_one()
        if not self.odoo_department_id:
            odoo_dept = self.env['hr.department'].create({
                'name': self.name,
                'company_id': self.company_id.id,
            })
            self.odoo_department_id = odoo_dept.id
        else:
            self.odoo_department_id.write({
                'name': self.name,
            })

        # Sync child departments
        for child in self.child_ids:
            child.action_sync_to_odoo()
            child.odoo_department_id.parent_id = self.odoo_department_id.id

        return True

    @api.model
    def cron_sync_departments(self):
        companies = self.env['res.company'].search([('is_wecom_integrated', '=', True)])
        for company in companies:
            self.with_context(company_id=company.id).sync_departments()

    def name_get(self):
        result = []
        for dept in self:
            name = dept.name
            if dept.parent_id:
                name = f"{dept.parent_id.name} / {name}"
            result.append((dept.id, name))
        return result

    @api.model
    def create(self, vals):
        department = super(WeComDepartment, self).create(vals)
        if not department.odoo_department_id:
            department.action_sync_to_odoo()
        return department

    def write(self, vals):
        result = super(WeComDepartment, self).write(vals)
        if 'name' in vals or 'parent_id' in vals:
            for department in self:
                department.action_sync_to_odoo()
        return result

    def unlink(self):
        for department in self:
            if department.odoo_department_id:
                department.odoo_department_id.unlink()
        return super(WeComDepartment, self).unlink()