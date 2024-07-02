# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.cache import ormcache

class WeComApplication(models.Model):
    """
    WeChat Work Application Model
    This model represents a WeChat Work application within Odoo.
    """
    _name = "wecom.application"
    _description = "WeChat Work Application"
    _inherit = ['wecom.base']
    _order = "sequence, id"

    name = fields.Char(compute="_compute_name", store=True, index=True, help="Full name of the application")
    app_name = fields.Char(required=True, translate=True, help="Name of the application")
    company_id = fields.Many2one("res.company", required=True, domain=[('is_wecom_organization', '=', True)], help="Company this application belongs to")
    type_id = fields.Many2one("wecom.app.type", required=True, help="Type of the application")
    category_ids = fields.Many2many("wecom.app.category", string="Categories", help="Categories this application belongs to")
    agent_id = fields.Integer(required=True, help="WeChat Work agent ID")
    secret = fields.Char(required=True, help="Application secret")
    sequence = fields.Integer(default=10, help="Sequence for ordering")

    webhook_ids = fields.One2many("wecom.app.webhook", "app_id", string="Webhooks", help="Webhooks associated with this application")
    setting_ids = fields.One2many("wecom.app.settings", "app_id", string="Settings", help="Settings for this application")

    _sql_constraints = [
        ("company_app_name_uniq", "unique (company_id, app_name)", _("The application name must be unique per company!")),
        ("company_agent_id_uniq", "unique (company_id, agent_id)", _("The Agent ID must be unique per company!"))
    ]

    @api.depends('company_id', 'app_name', 'type_id')
    def _compute_name(self):
        """Compute the full name of the application"""
        for app in self:
            app.name = f"{app.company_id.name}/{app.type_id.name}/{app.app_name}"

    @api.constrains('agent_id')
    def _check_agent_id(self):
        """Ensure agent_id is a positive integer"""
        for app in self:
            if app.agent_id <= 0:
                raise ValidationError(_("Agent ID must be a positive integer."))

    @api.model
    def create(self, vals):
        """Override create to clear cache"""
        res = super(WeComApplication, self).create(vals)
        self.clear_caches()
        return res

    def write(self, vals):
        """Override write to clear cache"""
        res = super(WeComApplication, self).write(vals)
        self.clear_caches()
        return res

    @ormcache('self.id')
    def get_access_token(self):
        """
        Get the access token for this application
        This method is cached for performance
        """
        # TODO: Implement actual token retrieval logic
        return "sample_token"

    def refresh_app_info(self):
        """Refresh application information from WeChat Work"""
        self.ensure_one()
        try:
            # TODO: Implement app info refresh logic
            self._logger.info(f"Refreshed info for app: {self.name}")
        except Exception as e:
            self.log_error(f"Failed to refresh app info: {str(e)}")
            raise ValidationError(_("Failed to refresh application information. Please try again later."))

    @api.model
    def cron_refresh_all_apps(self):
        """Cron job to refresh all applications"""
        apps = self.search([])
        for app in apps:
            try:
                app.refresh_app_info()
            except Exception as e:
                self._logger.error(f"Failed to refresh app {app.name}: {str(e)}")

    def action_view_webhooks(self):
        """Action to view related webhooks"""
        self.ensure_one()
        return {
            'name': _('Webhooks'),
            'view_mode': 'tree,form',
            'res_model': 'wecom.app.webhook',
            'domain': [('app_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_app_id': self.id}
        }