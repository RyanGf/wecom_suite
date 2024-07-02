# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WeComApiError(models.Model):
    _name = 'wecom.api.error'
    _description = 'WeChat Work API Error Log'
    _order = 'create_date desc'

    name = fields.Char(string='Error Name', required=True, index=True)
    app_id = fields.Many2one('wecom.application', string='WeChat Work App', required=True)
    error_code = fields.Char(string='Error Code', index=True)
    error_message = fields.Text(string='Error Message')
    api_endpoint = fields.Char(string='API Endpoint')
    request_data = fields.Text(string='Request Data')
    response_data = fields.Text(string='Response Data')
    create_date = fields.Datetime(string='Error Time', default=fields.Datetime.now, readonly=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored')
    ], string='Status', default='new', required=True)
    resolution_note = fields.Text(string='Resolution Note')
    user_id = fields.Many2one('res.users', string='Assigned To')

    def action_set_in_progress(self):
        self.write({'state': 'in_progress', 'user_id': self.env.user.id})

    def action_set_resolved(self):
        return {
            'name': _('Resolve Error'),
            'type': 'ir.actions.act_window',
            'res_model': 'wecom.api.error.resolve',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_error_id': self.id}
        }

    def action_set_ignored(self):
        self.write({'state': 'ignored'})

    @api.model
    def create(self, vals):
        record = super(WeComApiError, self).create(vals)
        self._notify_new_error(record)
        return record

    def _notify_new_error(self, error):
        # 发送通知给管理员或相关用户
        # 这里只是一个示例，你可能需要根据实际情况调整
        admin_group = self.env.ref('base.group_system')
        admin_partners = admin_group.users.mapped('partner_id')
        error.message_subscribe(partner_ids=admin_partners.ids)
        error.message_post(
            body=_("New WeChat Work API error recorded: [%(code)s] %(message)s") % {
                'code': error.error_code,
                'message': error.error_message
            },
            subject=_("New WeChat Work API Error"),
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

    @api.model
    def log_error(self, app, error_code, error_message, api_endpoint, request_data, response_data):
        self.create({
            'name': f"Error {error_code} - {api_endpoint}",
            'app_id': app.id,
            'error_code': error_code,
            'error_message': error_message,
            'api_endpoint': api_endpoint,
            'request_data': request_data,
            'response_data': response_data,
        })

    def get_error_statistics(self):
        stats = self.read_group(
            [],
            ['state'],
            ['state']
        )
        return {item['state']: item['state_count'] for item in stats}

class WeComApiErrorResolve(models.TransientModel):
    _name = 'wecom.api.error.resolve'
    _description = 'Resolve WeChat Work API Error'

    error_id = fields.Many2one('wecom.api.error', string='Error', required=True)
    resolution_note = fields.Text(string='Resolution Note', required=True)

    def action_resolve(self):
        self.ensure_one()
        if not self.error_id:
            raise UserError(_("No error specified."))
        self.error_id.write({
            'state': 'resolved',
            'resolution_note': self.resolution_note,
            'user_id': self.env.user.id
        })
        self.error_id.message_post(
            body=_("Error resolved: %s") % self.resolution_note,
            subject=_("Error Resolved"),
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        return {'type': 'ir.actions.act_window_close'}