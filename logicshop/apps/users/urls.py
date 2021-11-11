from django.urls import path, re_path

from . import views

app_name = 'users'

urlpatterns = [
    # 注册路由
    path('register/', views.RegisterView.as_view(), name='register'),
    # 判断用户名是否重复注册
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9-_]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断手机号是否重复注册
    re_path(r'^mobile/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view())
]
