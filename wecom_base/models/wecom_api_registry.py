# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WeComApiRegistry(models.Model):
    _name = 'wecom.api.registry'
    _description = 'WeChat Work API Registry'
    _order = 'name'

    name = fields.Char(string='API Name', required=True, index=True, help="Unique name of the API")
    endpoint = fields.Char(string='API Endpoint', required=True, help="The API endpoint path")
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE')
    ], string='HTTP Method', required=True, default='GET', help="HTTP method used for this API")
    description = fields.Text(string='Description', help="Detailed description of the API")
    required_params = fields.Text(string='Required Parameters', help="List of required parameters for the API")
    optional_params = fields.Text(string='Optional Parameters', help="List of optional parameters for the API")
    response_format = fields.Text(string='Response Format', help="Expected format of the API response")
    is_deprecated = fields.Boolean(string='Deprecated', default=False, help="Whether this API is deprecated")
    deprecated_reason = fields.Text(string='Deprecation Reason', help="Reason for deprecation, if applicable")
    alternative_api_id = fields.Many2one('wecom.api.registry', string='Alternative API',
                                         help="Suggested alternative API if this one is deprecated")
    category = fields.Selection([
        ('base', 'Base'),
        ('message', 'Message'),
        ('department', 'Department'),
        ('user', 'User'),
        ('media', 'Media'),
        ('oauth', 'OAuth'),
        ('external_contact', 'External Contact'),
        ('other', 'Other')
    ], string='Category', required=True, default='other', help="Category of the API")
    version = fields.Char(string='API Version', help="Version of the API")
    rate_limit = fields.Char(string='Rate Limit', help="Rate limit information for the API")
    needs_access_token = fields.Boolean(string='Needs Access Token', default=True,
                                        help="Whether this API requires an access token")

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'API name must be unique!')
    ]

    @api.constrains('is_deprecated', 'alternative_api_id')
    def _check_deprecation(self):
        for record in self:
            if record.is_deprecated and not record.alternative_api_id:
                raise ValidationError(_("Deprecated APIs should have an alternative API specified."))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.method})"
            if record.is_deprecated:
                name += " [DEPRECATED]"
            result.append((record.id, name))
        return result

    @api.model
    def get_api_details(self, api_name):
        api = self.search([('name', '=', api_name)], limit=1)
        if not api:
            return False
        return {
            'name': api.name,
            'endpoint': api.endpoint,
            'method': api.method,
            'description': api.description,
            'required_params': api.required_params,
            'optional_params': api.optional_params,
            'response_format': api.response_format,
            'is_deprecated': api.is_deprecated,
            'deprecated_reason': api.deprecated_reason,
            'alternative_api': api.alternative_api_id.name if api.alternative_api_id else False,
            'category': api.category,
            'version': api.version,
            'rate_limit': api.rate_limit,
            'needs_access_token': api.needs_access_token,
        }

    @api.model
    def register_api(self, vals):
        existing = self.search([('name', '=', vals.get('name'))])
        if existing:
            existing.write(vals)
            return existing.id
        else:
            return self.create(vals).id

    def toggle_deprecated(self):
        for record in self:
            record.is_deprecated = not record.is_deprecated

    @api.model
    def get_api_list_by_category(self, category=None):
        domain = []
        if category:
            domain.append(('category', '=', category))
        apis = self.search(domain)
        return [{
            'id': api.id,
            'name': api.name,
            'method': api.method,
            'is_deprecated': api.is_deprecated
        } for api in apis]

    @api.model
    def search_apis(self, keyword):
        return self.search([
            '|', '|',
            ('name', 'ilike', keyword),
            ('description', 'ilike', keyword),
            ('endpoint', 'ilike', keyword)
        ])

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = _("%s (copy)") % self.name
        return super(WeComApiRegistry, self).copy(default)

    @api.model
    def init_wecom_apis(self):
        # This method can be called to initialize or update the API registry
        apis_to_register = [
            {
                'name': 'get_access_token',
                'endpoint': 'gettoken',
                'method': 'GET',
                'description': 'Get access token for WeChat Work API',
                'category': 'base',
                'needs_access_token': False,
            },
            {
                'name': 'send_text_message',
                'endpoint': 'message/send',
                'method': 'POST',
                'description': 'Send a text message to WeChat Work users',
                'category': 'message',
            },
            # Add more APIs here
        ]
        for api in apis_to_register:
            self.register_api(api)

    def action_view_api_calls(self):
        # This method could be used to view API calls related to this API
        self.ensure_one()
        action = self.env.ref('wecom_base.action_wecom_api_call').read()[0]
        action['domain'] = [('api_id', '=', self.id)]
        action['context'] = {'default_api_id': self.id}
        return action