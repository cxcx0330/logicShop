import json
import re

from django import http
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, reverse
from django.views import View
from django_redis import get_redis_connection

from celery_tasks.email.tasks import send_verify_email
from utils.response_code import RETCODE
from utils.views import LoginRequiredJSONMixin
from . import constants
from .forms import RegisterForm, LoginForm
from .models import User, Address
from .utils import generate_verify_email_url, check_verify_email_token


# LAFEKSXRRAIVKTTG
# Create your views here.

class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def get(self, request):
        """展示修改密码界面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            request.user.check_password(old_password)
        except Exception as e:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg':'原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_password != new_password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})

        # 清理状态保持信息
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')

        # # 响应密码修改结果：重定向到登录界面
        return response

class UpdateTitleAddressView(LoginRequiredJSONMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


class DefaultAddressView(LoginRequiredJSONMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        # 用户表 default_address
        try:
            # user=request.user
            address = Address.objects.get(id=address_id)
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateDestoryAddressView(LoginRequiredJSONMixin, View):
    """更新和删除地址"""

    def put(self, request, address_id):
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 更新数据
        # address = Address.objects.get(id=address_id)
        # address.title = receiver
        # address.save()
        try:
            # update 返回受影响的行数
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '修改地址失败'})

        address = Address.objects.get(id=address_id)

        address_dict = {
            'id': address.id,
            'receiver': address.title,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        # 响应新的地址给前端渲染
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        # 逻辑删除(修改 is_deleted=True)
        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class AddressCreateView(LoginRequiredJSONMixin, View):
    """新增地址"""

    def post(self, request):
        """新增地址逻辑"""

        # 判断用户地址是否超过上限:查询当前登录用户的地址数量
        count = Address.objects.filter(user=request.user).count()
        if count > constants.USER_ADDRESS_COUNTS_LIMIT:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超出用户地址上限'})

        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 保存用户传入的数据
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )
            # 设置默认的收获地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()

        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        address_dict = {
            'id': address.id,
            'receiver': address.title,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供收货地址界面"""

        login_user = request.user
        # 查询登录用户的地址
        addresses = Address.objects.filter(user=login_user, is_deleted=False)
        address_list = []
        for address in addresses:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email
            }
            address_list.append(address_dict)
        context = {
            'addresses': address_list,
            'default_address_id': login_user.default_address_id
        }

        return render(request, 'user_center_site.html', context)


class VerifyEmailView(View):
    """验证邮箱"""

    def get(self, request):
        # 接收参数
        token = request.GET.get('token')
        if not token:
            return http.HttpResponseForbidden('缺少token')
        # 解密
        # 查询用户 email_active 是否已经激活
        user = check_verify_email_token(token)
        if user.email_active == 0:
            # 没有激活 email_active 设置为true
            user.email_active = True
            user.save()
        else:
            # email_active 是否已经激活
            return http.HttpResponseForbidden('邮箱已经被激活')

        # 响应结果
        return redirect(reverse('users:info'))


class EmailView(LoginRequiredJSONMixin, View):
    """添加邮箱"""

    def put(self, request):
        # put 请求方式，请求数据再body中
        # 接收email的参数
        # print(request)  字符串
        json_str = request.body.decode()
        # 转换成字典
        json_dict = json.loads(json_str)
        email = json_dict.get('email')

        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数邮箱错误')
        # 存数据
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
        # 发送邮件
        # subject = "商城邮箱验证"
        # html_message = '<p>尊敬的用户您好！</p>' \
        #                '<p>感谢您使用商城。</p>' \
        #                '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
        #                '<p><a href="%s">%s<a></p>' % (email, 'www.baidu.com', 'www.baidu.com')
        # send_mail(subject, '', from_email=settings.EMAIL_FROM, recipient_list=[email], html_message=html_message)
        # 使用celery异步发送邮件
        verify_url = generate_verify_email_url(request.user)
        send_verify_email.delay(email, verify_url)
        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


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
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', context=context)


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
