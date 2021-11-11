# celery 入口文件

from celery import Celery

# 创建celery实例

celery_app = Celery('lg')

# 加载配置文件

celery_app.config_from_object('celery_tasks.config')

# 注册任务 celery_tasks.sms.tasks
celery_app.autodiscover_tasks(['celery_tasks.sms'])

# 启动celery
# celery -A celery_tasks.main worker -l info

# windows 启动celery
# celery -A celery_tasks.main worker -l info --pool=solo
# 或者    安装eventlet
# celery -A celery_tasks.main worker -l info - P eventlet
