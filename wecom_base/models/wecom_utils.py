# -*- coding: utf-8 -*-

import string
import requests
import hashlib
import base64
import json
import time
import random
import xmltodict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from odoo import _, fields
from odoo.exceptions import ValidationError


def calculate_signature(token, timestamp, nonce, encrypt_msg):
    """
    计算签名
    :param token: 企业微信后台设置的 Token
    :param timestamp: 时间戳
    :param nonce: 随机字符串
    :param encrypt_msg: 加密后的消息体
    :return: 签名
    """
    sort_list = sorted([token, timestamp, nonce, encrypt_msg])
    sort_str = ''.join(sort_list)
    return hashlib.sha1(sort_str.encode()).hexdigest()


def encrypt_message(to_encrypt, encoding_aes_key):
    """
    加密消息
    :param to_encrypt: 要加密的消息
    :param encoding_aes_key: 企业微信后台设置的 EncodingAESKey
    :return: 加密后的消息
    """
    key = base64.b64decode(encoding_aes_key + "=")
    cipher = AES.new(key, AES.MODE_CBC, key[:16])
    encrypted = cipher.encrypt(pad(to_encrypt.encode(), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_message(encrypt_msg, encoding_aes_key):
    """
    解密消息
    :param encrypt_msg: 加密后的消息
    :param encoding_aes_key: 企业微信后台设置的 EncodingAESKey
    :return: 解密后的消息
    """
    key = base64.b64decode(encoding_aes_key + "=")
    cipher = AES.new(key, AES.MODE_CBC, key[:16])
    decrypted_msg = unpad(cipher.decrypt(base64.b64decode(encrypt_msg)), AES.block_size)
    return decrypted_msg[16:].decode('utf-8')


def parse_xml_to_dict(xml_string):
    """
    将XML字符串解析为字典
    :param xml_string: XML字符串
    :return: 解析后的字典
    """
    return xmltodict.parse(xml_string)['xml']


def dict_to_xml(dict_data):
    """
    将字典转换为XML字符串
    :param dict_data: 字典数据
    :return: XML字符串
    """
    xml = ['<xml>']
    for k, v in dict_data.items():
        if isinstance(v, str):
            xml.append(f'<{k}><![CDATA[{v}]]></{k}>')
        else:
            xml.append(f'<{k}>{v}</{k}>')
    xml.append('</xml>')
    return ''.join(xml)


def get_timestamp():
    """
    获取当前时间戳
    :return: 时间戳字符串
    """
    return str(int(time.time()))


def generate_random_string(length=16):
    """
    生成指定长度的随机字符串
    :param length: 字符串长度，默认16
    :return: 随机字符串
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def validate_wecom_params(params):
    """
    验证企业微信API调用参数
    :param params: API调用参数
    :return: None
    """
    required_params = ['corpid', 'corpsecret']
    for param in required_params:
        if param not in params or not params[param]:
            raise ValidationError(_("Missing required parameter: %s") % param)


def format_wecom_response(response):
    """
    格式化企业微信API响应
    :param response: API响应
    :return: 格式化后的响应
    """
    if response.get('errcode') != 0:
        raise ValidationError(_("WeChat Work API Error: [%(code)s] %(msg)s") % {
            'code': response.get('errcode'),
            'msg': response.get('errmsg')
        })
    return response


def handle_wecom_error(error):
    """
    处理企业微信API错误
    :param error: 错误信息
    :return: 格式化的错误消息
    """
    error_msg = str(error)
    if isinstance(error, requests.exceptions.RequestException):
        error_msg = _("Network error: %s") % error_msg
    elif isinstance(error, json.JSONDecodeError):
        error_msg = _("JSON decode error: %s") % error_msg
    return error_msg


def log_wecom_api_call(env, api_name, params, response):
    """
    记录企业微信API调用日志
    :param env: Odoo环境
    :param api_name: API名称
    :param params: 调用参数
    :param response: API响应
    """
    env['wecom.api.log'].sudo().create({
        'api_name': api_name,
        'params': json.dumps(params),
        'response': json.dumps(response),
        'call_time': fields.Datetime.now(),
    })


def is_valid_wecom_ip(ip_address):
    """
    验证IP地址是否为企业微信服务器IP
    :param ip_address: 要验证的IP地址
    :return: 是否为有效的企业微信服务器IP
    """
    # 这里应该实现实际的IP验证逻辑
    # 可以维护一个企业微信服务器IP列表，或者调用企业微信API获取最新的IP列表
    # 为了示例，这里简单返回True
    return True
