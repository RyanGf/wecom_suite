# -*- coding: utf-8 -*-

import logging
import hashlib
import hmac
import base64
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WeComAppWebhook(models.Model):
    """
    WeChat Work Application Webhook Model
    This model represents webhooks for WeChat Work applications, handling incoming messages and events.
    """
    _name = "wecom.app.webhook"
    _description = "WeChat Work Application Webhook"
    _inherit = ['wecom.base']

    name = fields.Char(string="Name", required=True, help="Name of the webhook")
    app_id = fields.Many2one('wecom.application', string="Application", required=True, ondelete='cascade',
                             help="Related WeChat Work application")
    url = fields.Char(string="Webhook URL", required=True, help="URL for receiving webhook events")
    token = fields.Char(string="Token", help="Token for verifying the source of messages")
    encoding_aes_key = fields.Char(string="EncodingAESKey", help="Key for message encryption and decryption")
    is_active = fields.Boolean(string="Active", default=True, help="Whether the webhook is active")
    last_called = fields.Datetime(string="Last Called", readonly=True, help="Timestamp of the last webhook call")

    _sql_constraints = [
        ('unique_app_webhook', 'unique(app_id, url)', 'Each application can only have one webhook with the same URL.')
    ]

    @api.constrains('encoding_aes_key')
    def _check_encoding_aes_key(self):
        for record in self:
            if record.encoding_aes_key and len(record.encoding_aes_key) != 43:
                raise ValidationError(_("EncodingAESKey must be 43 characters long."))

    def generate_webhook_url(self):
        """Generate the full webhook URL"""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/wecom_webhook/{self.id}"

    def verify_signature(self, signature, timestamp, nonce):
        """
        Verify the signature of incoming webhook requests
        :param signature: The signature to verify
        :param timestamp: The timestamp of the request
        :param nonce: A random nonce
        :return: True if the signature is valid, False otherwise
        """
        self.ensure_one()
        if not self.token:
            _logger.warning(f"Webhook {self.name} does not have a token set for signature verification.")
            return False
        string_to_sign = ''.join(sorted([self.token, timestamp, nonce]))
        hash_object = hashlib.sha1(string_to_sign.encode('utf-8'))
        calculated_signature = hash_object.hexdigest()
        return calculated_signature == signature

    def process_incoming_message(self, message):
        """
        Process incoming webhook messages
        :param message: The incoming message
        """
        self.ensure_one()
        try:
            # TODO: Implement message processing logic
            # This could involve decrypting the message, parsing its content,
            # and triggering appropriate actions in Odoo.
            _logger.info(f"Processing incoming message for webhook {self.name}")

            # Update last called timestamp
            self.write({'last_called': fields.Datetime.now()})

            # Example: You might want to create a record in another model based on the message
            # self.env['wecom.message.log'].create({
            #     'webhook_id': self.id,
            #     'message_content': message,
            #     'processed_at': fields.Datetime.now(),
            # })

            return True
        except Exception as e:
            _logger.error(f"Error processing incoming message for webhook {self.name}: {str(e)}")
            return False

    def encrypt_message(self, message, nonce, timestamp):
        """
        Encrypt outgoing messages
        :param message: The message to encrypt
        :param nonce: A random nonce
        :param timestamp: The current timestamp
        :return: Encrypted message
        """
        # TODO: Implement message encryption logic
        # This should use the encoding_aes_key to encrypt the message
        # according to WeChat Work's encryption specifications
        pass

    def decrypt_message(self, encrypted_message):
        """
        Decrypt incoming messages
        :param encrypted_message: The encrypted message to decrypt
        :return: Decrypted message
        """
        # TODO: Implement message decryption logic
        # This should use the encoding_aes_key to decrypt the message
        # according to WeChat Work's encryption specifications
        pass

    @api.model
    def create(self, vals):
        """Override create to generate webhook URL if not provided"""
        if 'url' not in vals:
            # Create the record first to get an ID
            record = super(WeComAppWebhook, self).create(vals)
            record.url = record.generate_webhook_url()
            return record
        return super(WeComAppWebhook, self).create(vals)

    def toggle_active(self):
        """Toggle the active status of the webhook"""
        for record in self:
            record.is_active = not record.is_active

    def test_webhook(self):
        """Test the webhook by sending a test message"""
        self.ensure_one()
        try:
            # TODO: Implement test message sending logic
            _logger.info(f"Sending test message to webhook {self.name}")
            # Here you would typically call the WeChat Work API to send a test message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Webhook Test"),
                    'message': _("Test message sent successfully."),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Error testing webhook {self.name}: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Webhook Test"),
                    'message': _("Failed to send test message. Check the logs for details."),
                    'type': 'danger',
                }
            }