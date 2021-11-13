from django import http
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, reverse
from django.views import View
from django_redis import get_redis_connection

from utils.response_code import RETCODE
from .forms import RegisterForm, LoginForm
from .models import User


# Create your views here.


class RegisterView(View):
    def get(self, request):
        """提供用户的注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """提供用户注册的逻辑"""
        # 校验参数 将前端传给后端的数据传递给RegisterForm 自定义的表单验证
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            # RegisterForm return cleaned_data
            username = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            mobile = register_form.cleaned_data.get('mobile')
            # 接收前端发给后端的 短信验证码 form表单
            sms_code_client = register_form.cleaned_data.get('sms_code')
            # 判断短信验证码是否正确
            redis_conn = get_redis_connection('verify_code')
            sms_code_server = redis_conn.get(f'sms_{mobile}')
            # 对比前端传过来的验证码与redis中的验证码
            if sms_code_server.decode() is None:
                return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
            if sms_code_server.decode() != sms_code_client:
                return render(request, 'register.html', {'sms_code_errmsg': '输入验证码有误'})
            # 创建用户，将用户保存到数据库中
            try:
                user = User.objects.create_user(username=username, password=password, mobile=mobile)
            except Exception as e:
                return render(request, 'register.html', {'register_errmsg': '注册失败'})

            # 状态保持
            login(request, user)
            # 响应注册结果
            return redirect(reverse('contents:index'))
        else:
            print(register_form.errors)
            context = {
                'forms_errors': register_form.errors
            }
            return render(request, 'register.html', context=context)


class LoginView(View):
    """用户名登录"""

    def get(self, request):
        """
        提供登录页面
        :param request:
        :return: 登录页面
        """
        return render(request, 'login.html')

    def post(self, request):
        """
        实现登录的后端业务逻辑
        :param request:
        :return:登录结果
        """
        # 接收请求，提取参数
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            remembered = login_form.cleaned_data.get('remembered')

            # 校验参数
            if not all([username, password]):
                return http.HttpResponseForbidden('缺少必传参数')

            # 自定义认证登录用户
            # user = User.objects.get(username=username)
            # pwd = user.password  # 数据库查询的密码位密文
            # print(user, pwd)
            #
            # # check_password(明文，密文)
            # if check_password(password, pwd):
            #     print('密码正确')
            # else:
            #     print('密码错误')

            # django中认证用户登录
            user = authenticate(username=username, password=password)
            # print(user) 查询出的用户
            if user is None:
                return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})

            # 状态保持
            login(request, user)

            if remembered is False:
                # 没有记住登录
                request.session.set_expiry(0)
            else:
                # 记住登录
                request.session.set_expiry(None)

            # 获取未登录时访问页面的next值，
            next = request.GET.get('next')
            # 存在next值时，直接跳转到未登录前访问的页面
            if next:
                response = redirect(next)
            else:
                # 不存在next值时，重定向到首页

                # 将用户名设置到cookie中，即可在首页显示用户名
                # response.set_cookie('key','value','expiry')
                response = redirect(reverse('contents:index'))
            # 　前端需要获取username
            response.set_cookie('username', user.username, max_age=3600 * 24)
            # 响应登录结果
            return response
        else:
            print(login_form.errors.get_json_data())
            context = {
                'form_errors': login_form.errors
            }
            return render(request, 'login.html', context=context)


class LogoutView(View):
    """用户推出登录"""

    def get(self, request):
        """实现用户推出登录的逻辑"""
        # 清楚状态保持信息
        logout(request)

        # 重定向
        response = redirect(reverse('contents:index'))
        # 删除cookie
        response.delete_cookie('username')

        return response


# 继承自LoginRequiredMixin这个类即可自动判断
class UserInfoView(LoginRequiredMixin, View):
    """用户个人中心"""
    # login_url = '/login/'

    def get(self, request):
        """
        提供个人中心页面
        :param request:
        :return:html页面
        """
        # http://127.0.0.1:8000/accounts/login/?next=/info/
        # LOGIN_URL = '/accounts/login/'  没有登录跳转的链接
        # next 未登录前正在访问页面的参数
        # login_url = 'info/'
        # if request.user.is_authenticated:
        #     # 用户已经登录
        #     return render(request, 'user_center_info.html')
        # else:
        #     # 未登录
        #     return redirect(reverse('users:login'))
        return render(request, 'user_center_info.html')


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    # username 是前端通过路由传递给后端的数据
    def get(self, request, username):
        """

        :param request:
        :param username: 用户名
        :return:返回用用户名是否重复，json
        """
        count = User.objects.filter(username=username).count()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


"""
                <div class="login_btn fl">
                    欢迎您：<em>居然</em>
                    <span>|</span>
                    <a href="#">退出</a>
                </div>
                <div class="login_btn fl">
                    <a href="login.html">登录</a>
                    <span>|</span>
                    <a href="register.html">注册</a>
                </div>
"""

"""
第一种实现方法：
                {% if user.is_authenticated %}
                <div class="login_btn fl">
                    欢迎您：<em>{{ user.username }}</em>
                    <span>|</span>
                    <a href="#">退出</a>
                </div>
                {% else %}
                <div class="login_btn fl">
                    <a href="{% url 'users:login' %}">登录</a>
                    <span>|</span>
                    <a href="{% url 'users:register' %}">注册</a>
                </div>
                {% endif %}
"""
