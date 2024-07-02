# -*- coding: utf-8 -*-

from . import models
from . import controllers

def post_init_hook(cr, registry):
    """Post-install script"""
    # 这里可以添加模块安装后需要执行的任何初始化代码
    pass

def uninstall_hook(cr, registry):
    """Uninstall script"""
    # 这里可以添加模块卸载时需要执行的清理代码
    pass