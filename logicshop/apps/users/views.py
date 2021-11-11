from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect, reverse
from django.views import View
from django_redis import get_redis_connection

from utils.response_code import RETCODE
from .forms import RegisterForm
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
