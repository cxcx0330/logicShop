# Create your views here.
import logging

from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect, render, reverse
from django.views import View
from django_redis import get_redis_connection

from users.models import User
from utils.response_code import RETCODE
from .models import OAuthQQUser
from .utils import generate_access_token, check_access_token

# 创建日志记录输出器
# dev中定义了一个django的日志记录器
logger = logging.getLogger('django')


class QQAuthUserView(View):
    """处理qq登录的回调"""

    def get(self, request):
        """处理qq登录回调的业务逻辑"""
        # 获取access_token 从回调的路径参数中获取code参数
        code = request.GET.get('code')
        if not code:
            return http.HttpResponseForbidden('获取code失败')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 使用code获取access_token
            access_token = oauth.get_access_token(code)

            # 使用access_token获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('oauth2.0认证失败！！')

        # openid qq用户的id
        # 使用openid判断该qq用户是否绑定商城用户 数据库查询
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 没有找到该用户 openid 未绑定商城用户 展示绑定用户的页面
            # 将openid以密文的方式渲染到前端页面中 access_token_openid 需要可逆的加密过程
            context = {'access_token_openid': generate_access_token(openid)}
            return render(request, 'oauth_callback.html', context=context)
        else:
            # 找到该记录 登录
            login(request, oauth_user.user)
            # 已经绑定与商城用户绑定，直接进行进行登录验证
            next = request.GET.get('state')
            response = redirect(next)
            response.set_cookie('username', oauth_user.user.username, max_age=3600 * 24)

            # 登录成功后合并购物车

            # 响应结果
            return response

    def post(self, request):
        """实现绑定用户的业务逻辑"""

        # 接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        access_token = request.POST.get('access_token_openid')

        # 校验参数
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get(f'sms_{mobile}')

        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效验证码'})
        if sms_code_server.decode() != sms_code_client:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '验证码有误'})

        # 判断openid是否有效
        openid = check_access_token(access_token)

        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': 'openid已经失效'})

        # 两种情况：第一种：手机号已经注册过来将其qq号与手机号用户进行绑定 第二种：用户不存在 创建新用户，与QQ进行绑定
        # 使用手机号查询对应的用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果不存在，创建新的用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            # 如果存在， 校验密码，
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '账号或者密码错误'})
        # 绑定用户
        try:
            oauth_qq_user = OAuthQQUser.objects.create(user=user, openid=openid)
        except Exception as e:
            return render(request, 'oauth_callback.html', {'account_errmsg': '账号或者密码错误'})
        # 登录成功后合并购物车

        # 重定向到首页
        login(request, oauth_qq_user.user)
        next = request.GET.get('state')
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', oauth_qq_user.user.username, max_age=3600 * 24)
        return response


class QQAuthURLView(View):
    """提供qq登录的扫码页面"""

    def get(self, request):
        next = request.GET.get('next')
        # print(next)
        # 创建生成qq登录链接的对象 需要在qq互联上认证
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        # 生成扫码的链接地址 将链接地址返回给前端进行跳转
        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})

# http://www.meiduo.site:8000/oauth_callback?code=38740CF53080D7F2A135359768115AD2&state=%2F
