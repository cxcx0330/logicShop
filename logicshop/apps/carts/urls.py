# @Time: 2021/11/28-10:10
# @User: Ycx
from django.urls import path

from . import views

app_name = 'carts'

urlpatterns = [
    # 商品添加购物车 路由
    path('carts/', views.CartsView.as_view(), name='info'),
    # 　全选购物车的路由
    path('carts/selection/', views.CartsSelectAllView.as_view())

]
