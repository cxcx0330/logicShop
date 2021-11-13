from django.urls import path

from . import views

app_name = 'oauth'

urlpatterns = [
    # 提供跳转QQ扫码登录页面的路由
    path('qq/login/', views.QQAuthURLView.as_view()),
    # qq登录的回调的路由
    path('oauth_callback/', views.QQAuthUserView.as_view())
]
