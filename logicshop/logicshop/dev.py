"""
Django settings for logicshop project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z7f4^diit3%a-*dw(t_7iy#f&41bb-lcu9%gxn(53e7$e9=g8a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['www.meiduo.site', '127.0.0.1']

# 　添加app的注册前缀路径 apps下面的app 添加导包路径
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Application definition
# 注册app
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'users',  # 用户模块
    'contents',  # 首页模块
    'verifications',  # 验证模块
    'oauth',  # 第三方登录模块
    'areas',  # 省市区三级联动
    'goods',  # 商品模块
    'haystack',  # 全文检索
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'logicshop.urls'

# 配置模板
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'builtins': ['django.templatetags.static'],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'logicshop.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# 配置数据库
DATABASES = {
    'default': {
        # mysql 5.7
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'logicshop',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': 3306
    }
}

# 配置redis缓存
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    # 　配置session
    "session": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    # 验证码
    "verify_code": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}

# 将session存放在redis中，在redis缓存中给session配置一号仓库
# SESSION_ENGINE修改保存session的机制，使用redis保存
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

# 配置静态文件  STATIC_URL 加载静态文件的 路径前缀 http://127.0.0.1:8000/static/images/1.png
STATIC_URL = '/static/'
# 静态文件的加载路径
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# 记录日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式（复杂，简单）
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/lgshop.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}

# 　指定自定义的用户模型，将自定义的用户模型类映射到数据库，而不是django自带的模型 app.模型
AUTH_USER_MODEL = 'users.User'

# 指定自定义的用户验证方法的位置（手机号与用户名验证）
AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileBackend']

# 判断用户是否登录，指定未登录用户的重定向地址
LOGIN_URL = '/login/'

# qq登录需要的配置文件
QQ_CLIENT_ID = '101913612'
QQ_CLIENT_SECRET = '39eb6ac28cb343b3e5562ef1032b7cab'
QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'

# 发送邮件配置
# 指定发送邮件的后端
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# 发送邮件的主机
EMAIL_HOST = 'smtp.163.com'
# 发送邮件的端口
EMAIL_PORT = 25
# 授权的邮箱
EMAIL_HOST_USER = 'ycx03301122@163.com'
# 授权码
EMAIL_HOST_PASSWORD = 'LAFEKSXRRAIVKTTG'
# 发件人的抬头
EMAIL_FROM = '管理员大爹<ycx03301122@163.com>'

# 　激活邮箱验证的主链接
EMAIL_VERIFY_URL = 'http://www.meiduo.site:8000/emails/verification/'

# 返回文件的路径
DEFAULT_FILE_STORAGE = 'utils.fastdfs.fdfs_storage.FastDFSStorage'
# 　文件路径
FAST_BASE_URL = 'http://118.178.232.251:8888/'

# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://118.178.232.251:9200/',  # Elasticsearch服务器ip地址，端口号固定为9200
        'INDEX_NAME': 'lgshop',  # Elasticsearch建立的索引库的名称
    },
}

# 当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# es查询到的数据 每页的数据量
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 5
