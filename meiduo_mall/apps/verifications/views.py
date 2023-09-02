from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
"""
前端：
    拼接一个url => 传给img的src => img发起请求
    url=http://ip:port/image_code/uuid/
后端：
    请求           接受路由中的uuid
    业务逻辑        生成图片验证码和图片二进制 => 通过redis保存图片
    响应           返回图片二进制
    
    路由： GET     image_code/uuid/
    1.接收uuid
    2.生成图片验证码和图片二进制
    3.通过redis保存图片
    4.返回图片二进制
"""
from django.views import View


class ImageCodeView(View):

    def get(self, request, uuid):
        # 1.接收uuid
        # 2.生成图片验证码和图片二进制
        from libs.captcha.captcha import captcha
        # text是图片内容  image是图片二进制
        text, image = captcha.generate_captcha()

        # 3.通过redis保存图片
        from django_redis import get_redis_connection
        # 链接redis数据库2，保存图片验证码数据
        redis_cli = get_redis_connection('code')
        # name: KeyT, time: ExpiryT, value: EncodableT
        redis_cli.setex(uuid, 100, text)

        # 4.返回图片二进制
        # 图片二进制，不能返回JSON数据
        # content_type=响应体数据类型  语法形式：大类/小类
        # content_type (MIME类型)
        # 例如：图片  image/jpeg, image/png, image/gif
        return HttpResponse(image, content_type='image/jpeg')


"""
1.注册
我们提供免费开发测试，【免费开发测试前，请先 注册 成为平台用户】。

2.绑定测试号
免费开发测试需要在"控制台—管理—号码管理—测试号码"绑定 测试号码 。

3.开发测试
开发测试过程请参考 短信业务接口 及 Demo示例 / sdk参考（新版）示例。Java环境安装请参考"新版sdk"。

4.免费开发测试注意事项
    4.1.免费开发测试需要使用到"控制台首页"，开发者主账户相关信息，如主账号、应用ID等。
    
    4.2.免费开发测试使用的模板ID为1，具体内容：【云通讯】您的验证码是{1}，请于{2}分钟内正确输入。其中{1}和{2}为短信模板参数。
    
    4.3.测试成功后，即可申请短信模板并 正式使用 。

"""

"""
/sms_codes/18283906566/?image_code=CSS8&image_code_id=c53accbf-4956-4e65-a75e-c599d63d909c

1.获取请求参数
2.验证参数
3.验证图片验证码
4.生成短信验证码
5.保存短信验证码
6.发送短信验证码
7.返回响应
"""


class SmsCodeView(View):

    def get(self, request, mobile):
        # 1.获取请求参数
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.验证参数
        if not all([image_code, uuid]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 3.验证图片验证码
        # 3.1 链接redis，获取redis数据
        from django_redis import get_redis_connection
        redis_cli = get_redis_connection('code')
        redis_image_code = redis_cli.get(uuid)
        if redis_image_code is None:
            return JsonResponse({'code': 400, 'errmsg': '图片验证码已过期'})
        # 3.2 对比验证码
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': 400, 'errmsg': '图片验证码错误'})

        # 提取发送短信的标记，查看是否验证码还在有效期内
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag is not None:
            return JsonResponse({'code': 400, 'errmsg': '不要频繁发送短信'})
        # 4.生成短信验证码
        from random import randint
        sms_code = '%04d' % randint(0, 9999)
        # 5.保存短信验证码
        redis_conn.setex(mobile, 300, sms_code)
        # 添加发送标记,有效期60s
        redis_conn.setex('send_flag_%s' % mobile, 60, 1)

        # 6.发送短信验证码
        # from libs.ronglian_sms_sdk.SmsSDK import SmsSDK
        # accId = '2c94811c8a27cf2d018a4c1f603a0e77'
        # accToken = '0219af12249c4869871525c79b97ebe4'
        # appId = '2c94811c8a27cf2d018a4c1f618f0e7e'
        # sdk = SmsSDK(accId, accToken, appId)
        # sdk.sendMessage('1', mobile, (sms_code, '5'))

        # celery实现短信异步发送
        from celery_tasks.sms.tasks import celery_send_sms_code
        # delay()参数等同于任务（函数）的参数
        celery_send_sms_code.delay(mobile, sms_code)

        # 7.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})
