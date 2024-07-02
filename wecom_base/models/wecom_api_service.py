# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WeComApiService(models.AbstractModel):
    _name = 'wecom.api.service'
    _description = 'WeChat Work API Service'

    @api.model
    def _get_access_token(self, app_id):
        """
        获取访问令牌
        :param app_id: WeChat Work 应用的ID
        :return: 访问令牌
        """
        app = self.env['wecom.application'].browse(app_id)
        if not app:
            raise UserError(_("WeChat Work application not found."))

        if app.access_token and app.token_expiration_time > fields.Datetime.now():
            return app.access_token

        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": app.company_id.wecom_corp_id,
            "corpsecret": app.secret
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("errcode") == 0:
                access_token = result.get("access_token")
                expires_in = result.get("expires_in", 7200)
                app.write({
                    'access_token': access_token,
                    'token_expiration_time': fields.Datetime.now() + timedelta(seconds=expires_in)
                })
                return access_token
            else:
                raise UserError(_("Failed to get access token: %s") % result.get("errmsg"))
        except requests.RequestException as e:
            _logger.error("Error while getting access token: %s", str(e))
            raise UserError(_("Network error while getting access token."))

    @api.model
    def call_api(self, app_id, endpoint, method='GET', params=None, data=None):
        """
        调用 WeChat Work API
        :param app_id: WeChat Work 应用的ID
        :param endpoint: API 端点
        :param method: HTTP 方法 ('GET' 或 'POST')
        :param params: URL 参数
        :param data: POST 数据
        :return: API 响应
        """
        access_token = self._get_access_token(app_id)
        url = f"https://qyapi.weixin.qq.com/cgi-bin/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        if params is None:
            params = {}
        params['access_token'] = access_token

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, data=json.dumps(data), headers=headers)
            else:
                raise UserError(_("Unsupported HTTP method: %s") % method)

            response.raise_for_status()
            result = response.json()

            if result.get("errcode") == 0:
                return result
            else:
                error_msg = _("WeChat Work API Error: [%(code)s] %(msg)s") % {
                    'code': result.get("errcode"),
                    'msg': result.get("errmsg")
                }
                _logger.error(error_msg)
                raise UserError(error_msg)

        except requests.RequestException as e:
            _logger.error("Error while calling WeChat Work API: %s", str(e))
            raise UserError(_("Network error while calling WeChat Work API."))

    @api.model
    def send_text_message(self, app_id, agent_id, content, to_user=None, to_party=None, to_tag=None):
        """
        发送文本消息
        :param app_id: WeChat Work 应用的ID
        :param agent_id: 应用的 agent_id
        :param content: 消息内容
        :param to_user: 接收消息的用户列表
        :param to_party: 接收消息的部门列表
        :param to_tag: 接收消息的标签列表
        :return: API 响应
        """
        data = {
            "touser": "|".join(to_user) if to_user else "@all",
            "toparty": "|".join(map(str, to_party)) if to_party else "",
            "totag": "|".join(map(str, to_tag)) if to_tag else "",
            "msgtype": "text",
            "agentid": agent_id,
            "text": {
                "content": content
            },
            "safe": 0
        }
        return self.call_api(app_id, "message/send", method="POST", data=data)

    # 可以添加更多特定的 API 调用方法，如发送其他类型的消息、管理部门、用户等

    @api.model
    def sync_departments(self, app_id):
        """
        同步部门列表
        :param app_id: WeChat Work 应用的ID
        :return: 同步结果
        """
        result = self.call_api(app_id, "department/list", method="GET")
        departments = result.get('department', [])

        # TODO: 实现部门同步逻辑
        # 这里你需要将获取到的部门信息与 Odoo 中的部门进行比对和更新

        return len(departments)

    @api.model
    def sync_users(self, app_id):
        """
        同步用户列表
        :param app_id: WeChat Work 应用的ID
        :return: 同步结果
        """
        result = self.call_api(app_id, "user/list", method="GET", params={"department_id": 1, "fetch_child": 1})
        users = result.get('userlist', [])

        # TODO: 实现用户同步逻辑
        # 这里你需要将获取到的用户信息与 Odoo 中的用户进行比对和更新

        return len(users)