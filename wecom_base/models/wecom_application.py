# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.cache import ormcache

class WeComApplication(models.Model):
    """
    企业微信应用模型
    此模型表示Odoo中的企业微信应用。
    """
    _name = "wecom.application"
    _description = "企业微信应用"
    _inherit = ['wecom.base']
    _order = "sequence, id"

    name = fields.Char(compute="_compute_name", store=True, index=True, help="应用的完整名称")
    app_name = fields.Char(required=True, translate=True, help="应用名称")
    company_id = fields.Many2one("res.company", required=True, domain=[('is_wecom_organization', '=', True)], help="应用所属的公司")
    type_id = fields.Many2one("wecom.app.type", required=True, help="应用类型")
    category_ids = fields.Many2many("wecom.app.category", string="分类", help="应用所属的分类")
    agent_id = fields.Integer(required=True, help="企业微信应用的AgentID")
    secret = fields.Char(required=True, help="应用的Secret")
    sequence = fields.Integer(default=10, help="用于排序的序号")

    webhook_ids = fields.One2many("wecom.app.webhook", "app_id", string="Webhooks", help="与此应用关联的Webhooks")
    setting_ids = fields.One2many("wecom.app.settings", "app_id", string="设置", help="此应用的设置")

    _sql_constraints = [
        ("company_app_name_uniq", "unique (company_id, app_name)", _("同一公司内应用名称必须唯一!")),
        ("company_agent_id_uniq", "unique (company_id, agent_id)", _("同一公司内AgentID必须唯一!"))
    ]

    @api.depends('company_id', 'app_name', 'type_id')
    def _compute_name(self):
        """计算应用的完整名称"""
        for app in self:
            app.name = f"{app.company_id.name}/{app.type_id.name}/{app.app_name}"

    @api.constrains('agent_id')
    def _check_agent_id(self):
        """确保agent_id是正整数"""
        for app in self:
            if app.agent_id <= 0:
                raise ValidationError(_("AgentID必须是正整数。"))

    @api.model
    def create(self, vals):
        """重写create方法以清除缓存"""
        res = super(WeComApplication, self).create(vals)
        self.clear_caches()
        return res

    def write(self, vals):
        """重写write方法以清除缓存"""
        res = super(WeComApplication, self).write(vals)
        self.clear_caches()
        return res

    @ormcache('self.id')
    def get_access_token(self):
        """
        获取此应用的访问令牌
        为了提高性能,此方法使用了缓存
        """
        # TODO: 实现实际的令牌获取逻辑
        return "sample_token"

    def refresh_app_info(self):
        """从企业微信刷新应用信息"""
        self.ensure_one()
        try:
            # TODO: 实现应用信息刷新逻辑
            self._logger.info(f"已刷新应用的信息: {self.name}")
        except Exception as e:
            self.log_error(f"刷新应用信息失败: {str(e)}")
            raise ValidationError(_("刷新应用信息失败。请稍后再试。"))

    @api.model
    def cron_refresh_all_apps(self):
        """刷新所有应用的定时任务"""
        apps = self.search([])
        for app in apps:
            try:
                app.refresh_app_info()
            except Exception as e:
                self._logger.error(f"刷新应用失败 {app.name}: {str(e)}")

    def action_view_webhooks(self):
        """查看相关Webhooks的动作"""
        self.ensure_one()
        return {
            'name': _('Webhooks'),
            'view_mode': 'tree,form',
            'res_model': 'wecom.app.webhook',
            'domain': [('app_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_app_id': self.id}
        }