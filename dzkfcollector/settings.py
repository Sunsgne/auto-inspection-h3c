import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-6^*k_8$el2(wux3hcu#yq@ac)n4arpy+w_n_#nfmqmnmp54v(8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'web',
    'drf_yasg',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dzkfcollector.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        #指定前端vue项目路径
        'DIRS': [os.path.join(BASE_DIR, 'frontend')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dzkfcollector.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "frontend/static"),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#框架自定义
REST_FRAMEWORK = {
    #指定全局异常处理类
    'EXCEPTION_HANDLER': 'web.golobal.exception_handler',
    #指定条件查询过滤器
    'DEFAULT_FILTER_BACKENDS': 'django_filters.rest_framework.backends.DjangoFilterBackend',
    #指定API文档
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema'
}

# swagger 配置项
SWAGGER_SETTINGS = {
    # 基础样式
    'SECURITY_DEFINITIONS': {
        "basic":{
            'type': 'basic'
        }
    },
    # 到处文件配置
    'DEFAULT_INFO': 'server.urls.openapi_info',
    "enabled_methods": [
        'get',
        'post',
        'put',
        'patch',
        'delete',
        'bulk_del',
    ],
    # 接口文档中方法列表以首字母升序排列
    'APIS_SORTER': 'alpha',
    # 如果支持json提交, 则接口文档中包含json输入框
    'JSON_EDITOR': True,
    # 方法列表字母排序
    'OPERATIONS_SORTER': 'alpha',
    'VALIDATOR_URL': None,
}

# TFTP服务器ip地址，需替换
SERVICE_TFTP_IP = os.getenv('ENV_TFTP_IP')
# SERVICE_TFTP_IP = '10.88.44.53'
# TFTP服务器文件存放目录
SERVICE_TFTP_FILE_PATH = '/var/lib/tftpboot/'
# 服务器采集文件映射目录
SERVICE_MAP_FILE_PATH = '/var/lib/iService'

# 配置日志模块
# 1.创建日志所在目录
# 创建日志保存文件地址
LOG_PATH = os.path.join(BASE_DIR, 'log')
# 如果地址日志文件夹不存在，则自动创建
if not os.path.isdir(LOG_PATH):
    os.mkdir(LOG_PATH)
# 2.定义LOGGING的格式
LOGGING = {
    # version只能为1
    'version': 1,
    # disable_existing_loggers 键为True（默认值），那么默认配置中的所有logger都将禁用
    # Logger的禁用与删除不同，logger依然存在，但是将默默丢弃任何传递给它的信息，也不会传播给上一级logger
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)-5s %(asctime)s [%(filename)-9s line %(lineno)-3s]: %(message)s'
        },
    },
    # 定义handler的格式
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',   # 文件重定向的配置，将打印到控制台的信息都重定向出去 python manage.py runserver >> /home/aea/log/test.log
            # 'stream': open('/home/aea/log/test.log','a'),  #虽然成功了，但是并没有将所有内容全部写入文件，目前还不清楚为什么
            'formatter': 'simple'   # 制定输出的格式，注意 在上面的formatters配置里面选择一个，否则会报错
        },
        'collect_handlers': {
            # 如果loggers的处理级别小于handlers的处理级别，则handler忽略该信息
            'level': 'DEBUG',
            # 指定文件类型为RotatingFileHandler，当日志文件的大小超过了maxBytes以后，就会自动切割
            'class': 'logging.handlers.RotatingFileHandler',
            # 输出文件地址
            'filename': '%s/linux-collecter.log' % LOG_PATH,
            # 使用哪一个日志格式化的配置
            'formatter': 'simple',
            # 指定日志文件的大小为5M，换算为1m=1024kb，1kb=1-24b
            'maxBytes': 1024 * 1024 * 5
        },
    },
    # 定义loggers的格式
    'loggers': {
        # 定义loggers的name
        'linux_collector': {
            'handlers': ['collect_handlers'],
            'level': 'INFO',
            # propagate=0,表示输出日志，但消息不传递
            # propagate=1是输出日志，同时消息往更高级别的地方传递。root为最高级别
            'propagate': False
        },
        'django': {
            'handlers': ['console'],
            # 这里直接输出到控制台只是请求的路由等系统console，当使用重定向之后会把所有内容输出到log日志
            'level': 'INFO',
            'propagate': True,
        },
    },
}
