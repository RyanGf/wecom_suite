# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_wecom_integrated = fields.Boolean(
        string="Integrate with WeChat Work",
        default=False,
        help="Check this box if this company is integrated with WeChat Work"
    )
    wecom_corp_id = fields.Char(
        string="WeChat Work CorpID",
        help="The unique identifier for your company's WeChat Work account"
    )
    wecom_agent_id = fields.Char(
        string="WeChat Work AgentID",
        help="The AgentID of your WeChat Work application"
    )
    wecom_secret = fields.Char(
        string="WeChat Work Secret",
        help="The secret key for your WeChat Work application"
    )
    wecom_token = fields.Char(
        string="WeChat Work Token",
        help="The token for message encryption and decryption"
    )
    wecom_aes_key = fields.Char(
        string="WeChat Work AES Key",
        help="The AES key for message encryption and decryption"
    )
    wecom_last_sync_time = fields.Datetime(
        string="Last Sync Time",
        readonly=True,
        help="The last time when data was synchronized with WeChat Work"
    )
    wecom_sync_interval = fields.Integer(
        string="Sync Interval (hours)",
        default=24,
        help="The interval in hours for automatic synchronization with WeChat Work"
    )

    @api.constrains('wecom_corp_id', 'wecom_agent_id', 'wecom_secret')
    def _check_wecom_credentials(self):
        for company in self:
            if company.is_wecom_integrated:
                if not (company.wecom_corp_id and company.wecom_agent_id and company.wecom_secret):
                    raise ValidationError(_("CorpID, AgentID, and Secret are required for WeChat Work integration."))

    def action_test_wecom_connection(self):
        self.ensure_one()
        if not self.is_wecom_integrated:
            raise ValidationError(_("WeChat Work integration is not enabled for this company."))

        # TODO: Implement the actual connection test
        # This should use the WeChat Work API to verify the credentials
        # For now, we'll just return a placeholder message

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Connection Test"),
                'message': _("Connection test functionality is not implemented yet."),
                'sticky': False,
                'type': 'warning',
            }
        }

    def action_sync_wecom_data(self):
        self.ensure_one()
        if not self.is_wecom_integrated:
            raise ValidationError(_("WeChat Work integration is not enabled for this company."))

        # TODO: Implement the actual data synchronization
        # This should sync users, departments, and other relevant data from WeChat Work
        # For now, we'll just update the last sync time

        self.wecom_last_sync_time = fields.Datetime.now()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Synchronization"),
                'message': _(
                    "Data synchronization functionality is not fully implemented yet. Last sync time updated."),
                'sticky': False,
                'type': 'warning',
            }
        }

    @api.model
    def cron_sync_wecom_data(self):
        companies = self.search([('is_wecom_integrated', '=', True)])
        for company in companies:
            try:
                company.action_sync_wecom_data()
            except Exception as e:
                _logger.error(f"Failed to sync WeChat Work data for company {company.name}: {str(e)}")

    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        if 'is_wecom_integrated' in vals or 'wecom_sync_interval' in vals:
            self._update_wecom_cron()
        return res

    def _update_wecom_cron(self):
        cron = self.env.ref('wecom_base.ir_cron_sync_wecom_data', raise_if_not_found=False)
        if cron:
            companies = self.search([('is_wecom_integrated', '=', True)])
            if companies:
                interval = min(companies.mapped('wecom_sync_interval'))
                cron.interval_number = interval
                cron.active = True
            else:
                cron.active = False