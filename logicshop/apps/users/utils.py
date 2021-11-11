import re

from django.contrib.auth.backends import ModelBackend

from .models import User


# 将使用用户名与手机号查询封装成一个方法
def get_user_by_account(account):
    """
    获取user对象
    :param account:用户名或者手机号
    :return: user
    """
    try:
        if re.match(r'^1[3-9]\d{9}', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except:
        return None
    else:
        return user


class UsernameMobileBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法
        :param request:
        :param username:用户名或手机号
        :param password:密码明文
        :param kwargs:额外参数
        :return:user
        """
        # 使用账号（用户名或手机号）查询用户
        # 手机号与传递过来的username匹配到

        # 如果查询到，校验密码
        # 密码校验成功，返回用户
        user = get_user_by_account(username)

        if user and user.check_password(password):
            return user
        else:
            return None
