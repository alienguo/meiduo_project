# 0.为Celery的运行设置Django环境
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.settings')

# 1.创建Celery实例
from celery import Celery
# 参数1：main设置脚本路径
app = Celery('celery_tasks')

# 2.设置broker
# 通过加载配置文件色设置broker
app.config_from_object('celery_tasks.config')

# 3.需要celery自动检测包的任务
# autodiscover_tasks 参数是列表，列表中的元素是task的路径
app.autodiscover_tasks(['celery_tasks.sms'])


# 4.消费者（虚拟环境终端执行）
# celery -A proj worker -l INFO
# celery -A celery_tasks.main worker -l INFO



