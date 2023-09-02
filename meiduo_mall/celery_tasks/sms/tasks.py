# 生产者----任务，函数
# 1.这个函数必须要让celery的实例的 task装饰器 装饰
# 2.需要celery自动检测包的任务
from libs.ronglian_sms_sdk import SmsSDK
from celery_tasks.main import app


@app.task
def celery_send_sms_code(mobile, sms_code):
    accId = '2c94811c8a27cf2d018a4c1f603a0e77'
    accToken = '0219af12249c4869871525c79b97ebe4'
    appId = '2c94811c8a27cf2d018a4c1f618f0e7e'
    sdk = SmsSDK(accId, accToken, appId)
    sdk.sendMessage('1', mobile, (sms_code, '5'))
