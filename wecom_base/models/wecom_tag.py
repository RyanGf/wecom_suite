# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class WeComTag(models.Model):
    _name = 'wecom.tag'
    _description = 'WeChat Work Tag'

    name = fields.Char(string='Tag Name', required=True)
    wecom_tagid = fields.Integer(string='WeChat Work Tag ID', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_ids = fields.Many2many('wecom.user', string='Tagged Users')
    department_ids = fields.Many2many('wecom.department', string='Tagged Departments')
    create_time = fields.Datetime(string='Create Time', readonly=True)
    order = fields.Integer(string='Order')
    type = fields.Selection([
        ('tag', 'User Tag'),
        ('group', 'Tag Group')
    ], string='Tag Type', default='tag')
    group_id = fields.Many2one('wecom.tag', string='Parent Tag Group', domain=[('type', '=', 'group')])
    child_tag_ids = fields.One2many('wecom.tag', 'group_id', string='Child Tags')

    _sql_constraints = [
        (
        'wecom_tagid_company_uniq', 'unique(wecom_tagid, company_id)', 'WeChat Work Tag ID must be unique per company!')
    ]

    @api.model
    def sync_tags(self):
        api_service = self.env['wecom.api.service']
        company = self.env.company

        try:
            response = api_service.call_api(company.id, 'tag/list', method='GET')
            if response.get('errcode') == 0:
                tags = response.get('taglist', [])
                self._process_tags(tags)
                return True
            else:
                raise UserError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
                    'code': response.get('errcode'),
                    'msg': response.get('errmsg')
                })
        except Exception as e:
            _logger.error(f"Failed to sync WeChat Work tags: {str(e)}")
            raise UserError(_("Failed to sync tags: %s") % str(e))

    def _process_tags(self, tags):
        for tag_data in tags:
            existing_tag = self.search(
                [('wecom_tagid', '=', tag_data['tagid']), ('company_id', '=', self.env.company.id)])
            vals = self._prepare_tag_values(tag_data)
            if existing_tag:
                existing_tag.write(vals)
            else:
                self.create(vals)

    def _prepare_tag_values(self, tag_data):
        return {
            'name': tag_data['tagname'],
            'wecom_tagid': tag_data['tagid'],
            'company_id': self.env.company.id,
            'create_time': fields.Datetime.now(),
            'order': tag_data.get('order', 0),
        }

    @api.model
    def cron_sync_tags(self):
        companies = self.env['res.company'].search([('is_wecom_integrated', '=', True)])
        for company in companies:
            self.with_context(company_id=company.id).sync_tags()

    def action_sync_users(self):
        self.ensure_one()
        api_service = self.env['wecom.api.service']

        try:
            response = api_service.call_api(self.company_id.id, 'tag/get', method='GET',
                                            params={'tagid': self.wecom_tagid})
            if response.get('errcode') == 0:
                user_list = response.get('userlist', [])
                department_list = response.get('partylist', [])
                self._update_tag_members(user_list, department_list)
                return True
            else:
                raise UserError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
                    'code': response.get('errcode'),
                    'msg': response.get('errmsg')
                })
        except Exception as e:
            _logger.error(f"Failed to sync tag members: {str(e)}")
            raise UserError(_("Failed to sync tag members: %s") % str(e))

    def _update_tag_members(self, user_list, department_list):
        users = self.env['wecom.user'].search(
            [('wecom_userid', 'in', [u['userid'] for u in user_list]), ('company_id', '=', self.company_id.id)])
        departments = self.env['wecom.department'].search(
            [('wecom_id', 'in', department_list), ('company_id', '=', self.company_id.id)])

        self.write({
            'user_ids': [(6, 0, users.ids)],
            'department_ids': [(6, 0, departments.ids)]
        })

    def action_add_users(self):
        return {
            'name': _('Add Users to Tag'),
            'type': 'ir.actions.act_window',
            'res_model': 'wecom.tag.add.users.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tag_id': self.id}
        }

    def action_remove_users(self):
        return {
            'name': _('Remove Users from Tag'),
            'type': 'ir.actions.act_window',
            'res_model': 'wecom.tag.remove.users.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tag_id': self.id}
        }


class WeComTagAddUsersWizard(models.TransientModel):
    _name = 'wecom.tag.add.users.wizard'
    _description = 'Add Users to WeChat Work Tag Wizard'

    tag_id = fields.Many2one('wecom.tag', string='Tag', required=True)
    user_ids = fields.Many2many('wecom.user', string='Users to Add')

    def action_add_users(self):
        self.ensure_one()
        api_service = self.env['wecom.api.service']

        try:
            userlist = self.user_ids.mapped('wecom_userid')
            response = api_service.call_api(self.tag_id.company_id.id, 'tag/addtagusers', method='POST', data={
                'tagid': self.tag_id.wecom_tagid,
                'userlist': userlist
            })
            if response.get('errcode') == 0:
                self.tag_id.write({'user_ids': [(4, user.id) for user in self.user_ids]})
                return {'type': 'ir.actions.act_window_close'}
            else:
                raise UserError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
                    'code': response.get('errcode'),
                    'msg': response.get('errmsg')
                })
        except Exception as e:
            raise UserError(_("Failed to add users to tag: %s") % str(e))


class WeComTagRemoveUsersWizard(models.TransientModel):
    _name = 'wecom.tag.remove.users.wizard'
    _description = 'Remove Users from WeChat Work Tag Wizard'

    tag_id = fields.Many2one('wecom.tag', string='Tag', required=True)
    user_ids = fields.Many2many('wecom.user', string='Users to Remove')

    def action_remove_users(self):
        self.ensure_one()
        api_service = self.env['wecom.api.service']

        try:
            userlist = self.user_ids.mapped('wecom_userid')
            response = api_service.call_api(self.tag_id.company_id.id, 'tag/deltagusers', method='POST', data={
                'tagid': self.tag_id.wecom_tagid,
                'userlist': userlist
            })
            if response.get('errcode') == 0:
                self.tag_id.write({'user_ids': [(3, user.id) for user in self.user_ids]})
                return {'type': 'ir.actions.act_window_close'}
            else:
                raise UserError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
                    'code': response.get('errcode'),
                    'msg': response.get('errmsg')
                })
        except Exception as e:
            raise UserError(_("Failed to remove users from tag: %s") % str(e))