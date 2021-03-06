from django.urls import path, re_path

from . import views

app_name = 'users'

urlpatterns = [
    # 用户注册 路由
    path('register/', views.RegisterView.as_view(), name='register'),
    # 判断用户名是否重复注册
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9-_]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断手机号是否重复注册
    re_path(r'^mobile/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # 用户登录路由
    path('login/', views.LoginView.as_view(), name='login'),
    # 退出登录路由
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # 用户个人中心路由
    path('info/', views.UserInfoView.as_view(), name='info'),
    # 保存邮箱的路由
    path('email/', views.EmailView.as_view(), name='email'),
    # 邮箱验证的链接
    path('emails/verification/', views.VerifyEmailView.as_view()),
    # 展示用户收货地址的路由
    path('addresses/', views.AddressView.as_view(), name='address'),
    # 新增用户地址的路由
    path('addresses/create/', views.AddressCreateView.as_view()),
    # 修改用户地址的路由
    re_path(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestoryAddressView.as_view()),
    # 设置默认地址的路由
    re_path(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),
    # 修改title的路由
    re_path(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateTitleAddressView.as_view()),
    # 修改密码的路由
    path('change_pwd/', views.ChangePasswordView.as_view(), name='password'),
    # 用户浏览记录
    path('browse_histories/', views.UserBrowserHistory.as_view())

]
