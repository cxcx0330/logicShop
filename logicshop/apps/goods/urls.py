# @Time: 2021/11/23-8:45
# @User: Ycx
from django.urls import re_path

from . import views

app_name = 'goods'
urlpatterns = [
    # 展示商品的列表页面
    re_path(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.GoodsListView.as_view(), name='list'),
    # 商品的热销排行
    re_path(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),
    # 商品的详情页面
    re_path(r'^detail/(?P<sku_id>\d+)/$', views.DetailGoodsView.as_view(), name='detail'),
    # 统计商品的访问量
    re_path(r'^detail/visit/(?P<category_id>\d+)/$', views.DetailVisitView.as_view()),
]
