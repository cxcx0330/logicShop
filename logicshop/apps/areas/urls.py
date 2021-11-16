# @Time: 2021/11/15-8:57
# @User: Ycx
from django.urls import path

from . import views

urlpatterns = [
    # 省市区三级联动 路由
    path('areas/', views.AreasView.as_view()),
]
