# @Time: 2021/11/23-8:45
# @User: Ycx
from django.urls import re_path

from . import views

app_name = 'goods'
urlpatterns = [
    # 展示商品的列表页面
    re_path(r'list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.GoodsListView.as_view(), name='list'),
    # 商品的热销排行
    re_path(r'hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view())
]
