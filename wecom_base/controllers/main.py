# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from ..models.wecom_utils import calculate_signature, decrypt_message, parse_xml_to_dict, is_valid_wecom_ip

_logger = logging.getLogger(__name__)

class WeComController(http.Controller):

    @http.route('/wecom/callback/<int:company_id>', type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def wecom_callback(self, company_id, **kwargs):
        company = request.env['res.company'].sudo().browse(company_id)
        if not company.exists():
            return 'Company not found', 404

        if not is_valid_wecom_ip(request.httprequest.remote_addr):
            _logger.warning(f"Received request from invalid IP: {request.httprequest.remote_addr}")
            return 'Invalid request', 403

        if request.httprequest.method == 'GET':
            return self._handle_get_request(company, **kwargs)
        elif request.httprequest.method == 'POST':
            return self._handle_post_request(company, **kwargs)

    def _handle_get_request(self, company, **kwargs):
        token = company.wecom_token
        try:
            signature = kwargs.get('msg_signature')
            timestamp = kwargs.get('timestamp')
            nonce = kwargs.get('nonce')
            echostr = kwargs.get('echostr')

            if not all([signature, timestamp, nonce, echostr]):
                return 'Missing parameters', 400

            calc_signature = calculate_signature(token, timestamp, nonce, echostr)
            if calc_signature != signature:
                return 'Invalid signature', 403

            return echostr
        except Exception as e:
            _logger.error(f"Error handling GET request: {str(e)}")
            return 'Internal server error', 500

    def _handle_post_request(self, company, **kwargs):
        token = company.wecom_token
        encoding_aes_key = company.wecom_encoding_aes_key
        try:
            signature = kwargs.get('msg_signature')
            timestamp = kwargs.get('timestamp')
            nonce = kwargs.get('nonce')

            if not all([signature, timestamp, nonce]):
                return 'Missing parameters', 400

            xml_data = request.httprequest.data
            calc_signature = calculate_signature(token, timestamp, nonce, xml_data.decode())
            if calc_signature != signature:
                return 'Invalid signature', 403

            decrypted_data = decrypt_message(xml_data, encoding_aes_key)
            message = parse_xml_to_dict(decrypted_data)

            self._process_message(company, message)

            return 'success'
        except Exception as e:
            _logger.error(f"Error handling POST request: {str(e)}")
            return 'Internal server error', 500

    def _process_message(self, company, message):
        message_type = message.get('MsgType')
        event = message.get('Event')

        if message_type == 'event':
            if event == 'change_contact':
                self._handle_contact_change_event(company, message)
            elif event == 'change_external_contact':
                self._handle_external_contact_change_event(company, message)
            # Add more event handlers as needed
        elif message_type == 'text':
            self._handle_text_message(company, message)
        # Add more message type handlers as needed

    def _handle_contact_change_event(self, company, message):
        change_type = message.get('ChangeType')
        if change_type == 'create_user':
            self._sync_new_user(company, message)
        elif change_type == 'update_user':
            self._update_user(company, message)
        elif change_type == 'delete_user':
            self._delete_user(company, message)
        # Add more contact change event handlers as needed

    def _handle_external_contact_change_event(self, company, message):
        change_type = message.get('ChangeType')
        if change_type == 'add_external_contact':
            self._add_external_contact(company, message)
        elif change_type == 'edit_external_contact':
            self._edit_external_contact(company, message)
        elif change_type == 'del_external_contact':
            self._delete_external_contact(company, message)
        # Add more external contact change event handlers as needed

    def _handle_text_message(self, company, message):
        # Process text messages
        # You might want to create a record, trigger an action, or send a response
        pass

    def _sync_new_user(self, company, message):
        # Sync new user to Odoo
        pass

    def _update_user(self, company, message):
        # Update existing user in Odoo
        pass

    def _delete_user(self, company, message):
        # Handle user deletion in Odoo
        pass

    def _add_external_contact(self, company, message):
        # Add new external contact to Odoo
        pass

    def _edit_external_contact(self, company, message):
        # Update existing external contact in Odoo
        pass

    def _delete_external_contact(self, company, message):
        # Handle external contact deletion in Odoo
        pass