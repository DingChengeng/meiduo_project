# celery入口
from celery import Celery


# 创建celery 实例、生产者
celery_app = Celery('meiduo')

# 告诉生产者中间人的位置
celery_app.config_from_object('celery_tasks.config')

# 注册任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])
