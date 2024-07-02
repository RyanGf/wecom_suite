# -*- coding: utf-8 -*-

import json
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WeComMessage(models.Model):
    _name = 'wecom.message'
    _description = 'WeChat Work Message'
    _order = 'create_date DESC'

    name = fields.Char(string='Message ID', required=True, readonly=True, copy=False, default='New')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    message_type = fields.Selection([
        ('text', 'Text'),
        ('image', 'Image'),
        ('voice', 'Voice'),
        ('video', 'Video'),
        ('file', 'File'),
        ('textcard', 'Text Card'),
        ('news', 'News'),
        ('mpnews', 'MP News'),
        ('markdown', 'Markdown'),
        ('miniprogram', 'Mini Program Notice'),
        ('taskcard', 'Task Card'),
    ], string='Message Type', required=True, default='text')
    content = fields.Text(string='Content')
    recipient_type = fields.Selection([
        ('user', 'User'),
        ('party', 'Department'),
        ('tag', 'Tag'),
    ], string='Recipient Type', required=True, default='user')
    recipient_ids = fields.Char(string='Recipient IDs', help="Comma-separated IDs of recipients")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', readonly=True)
    send_time = fields.Datetime(string='Send Time', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('wecom.message') or 'New'
        return super(WeComMessage, self).create(vals)

    def action_send(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft messages can be sent."))

        try:
            self._send_message()
            self.write({
                'state': 'sent',
                'send_time': fields.Datetime.now(),
            })
        except Exception as e:
            self.write({
                'state': 'failed',
                'error_message': str(e),
            })
            _logger.error(f"Failed to send WeChat Work message: {str(e)}")
            raise UserError(_("Failed to send message: %s") % str(e))

    def _send_message(self):
        self.ensure_one()
        api_service = self.env['wecom.api.service']

        message_data = {
            'msgtype': self.message_type,
            self.message_type: self._prepare_message_content(),
        }

        if self.recipient_type == 'user':
            message_data['touser'] = self.recipient_ids
        elif self.recipient_type == 'party':
            message_data['toparty'] = self.recipient_ids
        elif self.recipient_type == 'tag':
            message_data['totag'] = self.recipient_ids

        app = self.env['wecom.application'].search([('company_id', '=', self.company_id.id)], limit=1)
        if not app:
            raise UserError(_("No WeChat Work application configured for this company."))

        response = api_service.call_api(app.id, 'message/send', method='POST', data=message_data)
        if response.get('errcode') != 0:
            raise UserError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
                'code': response.get('errcode'),
                'msg': response.get('errmsg')
            })

    def _prepare_message_content(self):
        self.ensure_one()
        if self.message_type == 'text':
            return {'content': self.content}
        elif self.message_type in ['textcard', 'news', 'mpnews', 'markdown']:
            return json.loads(self.content)
        else:
            # For other types, you might need to handle file uploads or other specific content
            raise NotImplementedError(_("Message type %s is not implemented yet.") % self.message_type)

    @api.model
    def process_incoming_message(self, message_data):
        # This method would be called by your webhook controller
        # to process incoming messages from WeChat Work
        _logger.info(f"Received WeChat Work message: {message_data}")
        # TODO: Implement message processing logic
        # This could involve creating a record, triggering actions, etc.
        return True


class WeComMessageTemplate(models.Model):
    _name = 'wecom.message.template'
    _description = 'WeChat Work Message Template'

    name = fields.Char(string='Template Name', required=True)
    message_type = fields.Selection(related='message_id.message_type', readonly=True)
    content = fields.Text(string='Template Content')
    message_id = fields.Many2one('wecom.message', string='Base Message', required=True)

    def action_use_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wecom.message',
            'view_mode': 'form',
            'context': {
                'default_message_type': self.message_type,
                'default_content': self.content,
            },
            'target': 'new',
        }