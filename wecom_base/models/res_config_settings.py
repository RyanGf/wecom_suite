# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wecom_corp_id = fields.Char(string="WeChat Work Corp ID", config_parameter='wecom.corp_id')
    wecom_agent_id = fields.Char(string="WeChat Work Agent ID", config_parameter='wecom.agent_id')
    wecom_secret = fields.Char(string="WeChat Work Secret", config_parameter='wecom.secret')
    wecom_token = fields.Char(string="WeChat Work Token", config_parameter='wecom.token')
    wecom_aes_key = fields.Char(string="WeChat Work AES Key", config_parameter='wecom.aes_key')

    wecom_api_base_url = fields.Char(
        string="WeChat Work API Base URL",
        config_parameter='wecom.api_base_url',
        default='https://qyapi.weixin.qq.com/cgi-bin/'
    )

    wecom_enable_user_sync = fields.Boolean(
        string="Enable User Synchronization",
        config_parameter='wecom.enable_user_sync'
    )
    wecom_user_sync_interval = fields.Integer(
        string="User Sync Interval (hours)",
        config_parameter='wecom.user_sync_interval',
        default=24
    )

    wecom_enable_department_sync = fields.Boolean(
        string="Enable Department Synchronization",
        config_parameter='wecom.enable_department_sync'
    )
    wecom_department_sync_interval = fields.Integer(
        string="Department Sync Interval (hours)",
        config_parameter='wecom.department_sync_interval',
        default=24
    )

    wecom_enable_message_push = fields.Boolean(
        string="Enable Message Push",
        config_parameter='wecom.enable_message_push'
    )

    wecom_log_level = fields.Selection([
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
        ('debug', 'Debug')
    ], string="Log Level", config_parameter='wecom.log_level', default='error')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            wecom_corp_id=get_param('wecom.corp_id'),
            wecom_agent_id=get_param('wecom.agent_id'),
            wecom_secret=get_param('wecom.secret'),
            wecom_token=get_param('wecom.token'),
            wecom_aes_key=get_param('wecom.aes_key'),
            wecom_api_base_url=get_param('wecom.api_base_url', 'https://qyapi.weixin.qq.com/cgi-bin/'),
            wecom_enable_user_sync=get_param('wecom.enable_user_sync', False),
            wecom_user_sync_interval=int(get_param('wecom.user_sync_interval', 24)),
            wecom_enable_department_sync=get_param('wecom.enable_department_sync', False),
            wecom_department_sync_interval=int(get_param('wecom.department_sync_interval', 24)),
            wecom_enable_message_push=get_param('wecom.enable_message_push', False),
            wecom_log_level=get_param('wecom.log_level', 'error'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('wecom.corp_id', self.wecom_corp_id)
        set_param('wecom.agent_id', self.wecom_agent_id)
        set_param('wecom.secret', self.wecom_secret)
        set_param('wecom.token', self.wecom_token)
        set_param('wecom.aes_key', self.wecom_aes_key)
        set_param('wecom.api_base_url', self.wecom_api_base_url)
        set_param('wecom.enable_user_sync', self.wecom_enable_user_sync)
        set_param('wecom.user_sync_interval', self.wecom_user_sync_interval)
        set_param('wecom.enable_department_sync', self.wecom_enable_department_sync)
        set_param('wecom.department_sync_interval', self.wecom_department_sync_interval)
        set_param('wecom.enable_message_push', self.wecom_enable_message_push)
        set_param('wecom.log_level', self.wecom_log_level)

    @api.onchange('wecom_enable_user_sync')
    def _onchange_wecom_enable_user_sync(self):
        if self.wecom_enable_user_sync:
            self.wecom_enable_department_sync = True

    def action_wecom_test_connection(self):
        # TODO: Implement connection test
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Connection Test',
                'message': 'Connection test not implemented yet.',
                'sticky': False,
            }
        }

    def action_wecom_sync_now(self):
        # TODO: Implement immediate sync
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync',
                'message': 'Immediate sync not implemented yet.',
                'sticky': False,
            }
        }