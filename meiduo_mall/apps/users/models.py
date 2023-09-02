from django.db import models

# Create your models here.

# 1. 自己定义模型
# 密码需要加密，并实现登录时密码验证
# class User(models.Model):
#     username = models.CharField(max_length=20, unique=True)
#     password = models.CharField(max_length=20)
#     mobile = models.CharField(max_length=11, unique=True)

# 2.django自带用户模型
# 有密码的加密和密码的验证
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True)
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name
