from django.shortcuts import render

# Create your views here.
import re
import json
from django.views import View
from apps.users.models import User
from django.http import JsonResponse


class UsernameCountView(View):

    def get(self, request, username):
        # 1.接收用户名，对这个用户名进行判断
        # if not re.match('[a-zA-Z0-9_-]{5,20}', username):
        #     return JsonResponse({'code': 200, 'errmsg': '用户名不满足需求'})
        # 2.根据用户名查询数据库
        count = User.objects.filter(username=username).count()
        # 3.返回响应
        return JsonResponse({'code': 0, 'count': count, 'errmsg': 'ok'})


class MobileCountView(View):

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'count': count})


class RegisterView(View):

    def post(self, request):
        # 1.接收请求（POST---JSON）
        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)

        # 2.获取数据
        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        allow = body_dict.get('allow')

        # 3.验证数据
        #   3.1 用户名，密码，确认密码，手机号，是否同意协议都需要有
        if not all([username, password, password2, mobile]):   # all是一个函数，用于判断是否数组中所有元素都为真
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})
        #   3.2 用户名满足规则，用户名不能重复
        if not re.match('[a-zA-Z0-9_-]{5,20}', username):
            return JsonResponse({'code': 400, 'errmsg': '用户名不满足规则'})
        #   3.3 密码满足规则
        if not 20 >= len(password) >= 8:
            return JsonResponse({'code': 400, 'errmsg': '密码不满足规则'})
        #   3.4 确认密码和密码要一致
        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '两次密码不一致'})
        #   3.5 手机号码满足规则，手机号码也不能重复
        if not re.match(r'1[3-9]\d{9}', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号不满足规则'})
        #   3.6 需要同意协议
        if not allow:
            return JsonResponse({'code': 400, 'errmsg': '请勾选用户使用协议'})

        # 判断短信验证码是否正确：跟图形验证码的验证一样的逻辑
        sms_code = body_dict.get('sms_code')
        # 提取服务端存储的短信验证码：以前怎么存储，现在就怎么提取
        from django_redis import get_redis_connection
        redis_cli = get_redis_connection('verify_code')
        sms_code_server = redis_cli.get(mobile)  # sms_code_server是bytes
        # 判断短信验证码是否过期
        if not sms_code_server:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码失效'})
        # 对比用户输入的和服务端存储的短信验证码是否一致
        if sms_code != sms_code_server.decode():
            return JsonResponse({'code': 400, 'errmsg': '短信验证码有误'})

        # 4.数据入库
        # 密码不会加密
        # User.objects.create(username=username, password=password, mobile=mobile)
        # 密码加密
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 1.session设置（request.set_session()）
        # 2.django提供了状态保持的方法
        from django.contrib.auth import login

        login(request, user)

        # 5.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


class LoginView(View):

    def post(self, request):
        # 1.接收数据
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        remembered = data.get('remembered')

        # 2.验证数据
        if not all([username, password]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 确定是根据手机号查询还是用户名查询
        # 修改User.USERNAME_FIELD来影响authenticate查询
        # authenticate查询就是根据User.USERNAME_FIELD字段
        if re.match(r'1[3-9]\d{9}', username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        # 3.验证用户名和密码是否正确
        # 方式一：查询数据库
        # 方式二：django提供的方法
        from django.contrib.auth import authenticate
        # authenticate 传递用户名和密码 正确返回用户信息，错误返回None
        user = authenticate(username=username, password=password)
        if user is None:
            return JsonResponse({'code': 400, 'errmsg': '账号或密码错误'})

        # 4.session
        from django.contrib.auth import login

        login(request, user)

        # 5.判断是否记住登录(免登录，不只是记住账号和密码)
        if remembered:
            # 默认两周（None），根据产品实际情况可以进行修改
            request.session.set_expiry(None)
        else:
            # 不记住，浏览器关闭session过期
            request.session.set_expiry(0)

        # 6.返回响应
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        # 设置cookie信息 为了首页显示用户信息
        response.set_cookie('username', username)

        return response

