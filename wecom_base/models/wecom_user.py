# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class WeComUser(models.Model):
    _name = 'wecom.user'
    _description = 'WeChat Work User'
    _inherits = {'res.users': 'odoo_user_id'}
    _rec_name = 'name'

    odoo_user_id = fields.Many2one('res.users', string='Odoo User', required=True, ondelete='cascade')
    wecom_userid = fields.Char(string='WeChat Work UserID', required=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    department_ids = fields.Many2many('wecom.department', string='Departments')
    position = fields.Char(string='Position')
    mobile = fields.Char(string='Mobile')
    gender = fields.Selection([
        (1, 'Male'),
        (2, 'Female'),
        (0, 'Unspecified')
    ], string='Gender')
    email = fields.Char(string='Email')
    is_leader_in_dept = fields.Char(string='Leader in Departments')
    avatar = fields.Binary(string='Avatar')
    thumb_avatar = fields.Binary(string='Thumb Avatar')
    telephone = fields.Char(string='Telephone')
    alias = fields.Char(string='Alias')
    extattr = fields.Text(string='Extended Attributes')
    status = fields.Selection([
        (1, 'Active'),
        (2, 'Deactivated'),
        (4, 'Unassigned')
    ], string='Status', default=1)
    qr_code = fields.Binary(string='QR Code')
    external_profile = fields.Text(string='External Profile')
    external_position = fields.Char(string='External Position')

    _sql_constraints = [
        ('wecom_userid_company_uniq', 'unique(wecom_userid, company_id)',
         'WeChat Work UserID must be unique per company!')
    ]

    @api.model
    def sync_users(self):
        api_service = self.env['wecom.api.service']
        company = self.env.company

        try:
            response = api_service.call_api(company.id, 'user/list', method='GET',
                                            params={'department_id': 1, 'fetch_child': 1})
            if response.get('errcode') == 0:
                users = response.get('userlist', [])
                self._process_users(users)
                return True
            else:
                raise UserError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
                    'code': response.get('errcode'),
                    'msg': response.get('errmsg')
                })
        except Exception as e:
            _logger.error(f"Failed to sync WeChat Work users: {str(e)}")
            raise UserError(_("Failed to sync users: %s") % str(e))

    def _process_users(self, users):
        for user_data in users:
            existing_user = self.search(
                [('wecom_userid', '=', user_data['userid']), ('company_id', '=', self.env.company.id)])
            vals = self._prepare_user_values(user_data)
            if existing_user:
                existing_user.write(vals)
            else:
                self.create(vals)

    def _prepare_user_values(self, user_data):
        departments = self.env['wecom.department'].search(
            [('wecom_id', 'in', user_data.get('department', [])), ('company_id', '=', self.env.company.id)])

        # Prepare Odoo user values
        odoo_user_vals = {
            'name': user_data['name'],
            'login': user_data['userid'],
            'email': user_data.get('email', ''),
            'company_id': self.env.company.id,
        }

        # Create or update Odoo user
        odoo_user = self.env['res.users'].search([('login', '=', user_data['userid'])], limit=1)
        if odoo_user:
            odoo_user.write(odoo_user_vals)
        else:
            odoo_user = self.env['res.users'].create(odoo_user_vals)

        return {
            'odoo_user_id': odoo_user.id,
            'wecom_userid': user_data['userid'],
            'company_id': self.env.company.id,
            'department_ids': [(6, 0, departments.ids)],
            'position': user_data.get('position', ''),
            'mobile': user_data.get('mobile', ''),
            'gender': user_data.get('gender', 0),
            'email': user_data.get('email', ''),
            'is_leader_in_dept': ','.join(map(str, user_data.get('is_leader_in_dept', []))),
            'avatar': user_data.get('avatar', ''),
            'thumb_avatar': user_data.get('thumb_avatar', ''),
            'telephone': user_data.get('telephone', ''),
            'alias': user_data.get('alias', ''),
            'extattr': str(user_data.get('extattr', {})),
            'status': user_data.get('status', 1),
            'qr_code': user_data.get('qr_code', ''),
            'external_profile': str(user_data.get('external_profile', {})),
            'external_position': user_data.get('external_position', ''),
        }

    @api.model
    def cron_sync_users(self):
        companies = self.env['res.company'].search([('is_wecom_integrated', '=', True)])
        for company in companies:
            self.with_context(company_id=company.id).sync_users()

    def action_sync_to_odoo(self):
        self.ensure_one()
        self.odoo_user_id.write({
            'name': self.name,
            'email': self.email,
            # Add other fields as needed
        })
        return True

    @api.model
    def create(self, vals):
        user = super(WeComUser, self).create(vals)
        user.action_sync_to_odoo()
        return user

    def write(self, vals):
        result = super(WeComUser, self).write(vals)
        for user in self:
            user.action_sync_to_odoo()
        return result

    def unlink(self):
        for user in self:
            user.odoo_user_id.active = False
        return super(WeComUser, self).unlink()