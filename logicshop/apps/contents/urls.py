from django.urls import path

from . import views

app_name = 'contents'

urlpatterns = [
    # 首页
    path('', views.IndexView.as_view(), name='index')
]
