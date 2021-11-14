from django import http
from django.contrib.auth.mixins import LoginRequiredMixin

from .response_code import RETCODE


class LoginRequiredJSONMixin(LoginRequiredMixin):
    """自定义判断用户是否登录的扩展类，return：json"""

    def handle_no_permission(self):
        """直接响应返回json数据"""
        return http.JsonResponse({'code': RETCODE.SESSIONERR, 'err_msg': '用户未登录'})
