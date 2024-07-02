# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WeComBase(models.AbstractModel):
    """
    WeChat Work Base Model
    This abstract model provides common fields and methods for all WeChat Work related models.
    """
    _name = 'wecom.base'
    _description = 'WeChat Work Base Model'

    active = fields.Boolean(default=True, help="Whether the record is active")

    def log_error(self, error_message):
        """
        Log an error message
        :param error_message: The error message to log
        """
        _logger.error(f"{self._name}: {error_message}")

    @api.model
    def create(self, vals):
        """
        Override create method to add error logging
        :param vals: The values to create the record with
        :return: The created record
        """
        try:
            return super(WeComBase, self).create(vals)
        except Exception as e:
            self.log_error(f"Create failed: {str(e)}")
            raise

    def write(self, vals):
        """
        Override write method to add error logging
        :param vals: The values to update the record with
        :return: True if the update was successful
        """
        try:
            return super(WeComBase, self).write(vals)
        except Exception as e:
            self.log_error(f"Write failed: {str(e)}")
            raise

    def get_wecom_config(self):
        """
        Get WeChat Work configuration
        :return: A dictionary containing WeChat Work configuration
        """
        # TODO: Implement configuration retrieval logic
        return {}

    @api.model
    def format_wecom_response(self, response):
        """
        Format WeChat Work API response
        :param response: The raw API response
        :return: Formatted response
        """
        # TODO: Implement response formatting logic
        return response

    def handle_wecom_error(self, error):
        """
        Handle WeChat Work API error
        :param error: The error object or message
        """
        error_message = str(error)
        self.log_error(f"WeChat Work API Error: {error_message}")
        raise ValidationError(_(f"WeChat Work API Error: {error_message}"))