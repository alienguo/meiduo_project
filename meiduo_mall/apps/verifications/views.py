from django.http import HttpResponse
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
