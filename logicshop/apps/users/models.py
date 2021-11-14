from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class User(AbstractUser):
    """自定义的用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    # 追加邮箱是否激活的字段
    email_active = models.BooleanField(verbose_name='邮箱验证的状态', default=False)

    class Meta:
        db_table = 'tb_users'
        # admin 后台需要使用的
        verbose_name = '用户'
        verbose_name_plural = verbose_name
