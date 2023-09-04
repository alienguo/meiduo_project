from django.shortcuts import render

# Create your views here.
import re
import json
from django.views import View
from apps.users.models import User, Address
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


"""
前端：
    当用户点击退出按钮时，前端发送axios delete请求
    
后端：
    请求
    业务逻辑   退出
    响应
"""


class LogoutView(View):

    def delete(self, request):
        from django.contrib.auth import logout
        # 1.删除session信息
        logout(request)
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        # 2.删除cookie信息 前端是根据cookie信息来判断用户是否登录的
        response.delete_cookie('username')
        return response


"""
LoginRequiredMixin 未登录的用户会返回 重定向。重定向并不是JSON数据
需要返回JSON数据
"""
from utils.views import LoginRequiredJSONMixin


class CenterView(LoginRequiredJSONMixin, View):

    def get(self, request):
        info_data = {
            'username': request.user.username,   # request.user就是已经登录的用户信息
            'email': request.user.email,
            'mobile': request.user.mobile,
            'email_active': request.user.email_active,
        }

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'info_data': info_data})


class EmailView(LoginRequiredJSONMixin, View):

    def put(self, request):
        # 1.接收参数
        data = json.loads(request.body.decode())
        email = data.get('email')

        # 2.验证参数
        if not email:
            return JsonResponse({'code': 400, 'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w.-]*@[a-z0-9-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        # 3.保存邮箱地址（更新）
        user = request.user
        user.email = email
        user.save()

        # 4.发送邮件
        from django.core.mail import send_mail
        # subject   主题
        subject = '美多商城激活邮件'
        # message   邮件内容
        message = ''
        # from_email    发件人
        from_email = '美多商城<qi_rui_hua@163.com>'
        # recipient_list    收件人列表
        recipient_list = [email]

        # 4.1加密处理
        from apps.users.utils import generic_email_verify_token
        token = generic_email_verify_token(request.user.id)

        # 4.2编写激活邮件
        verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=%s' % token
        # 邮件内容是html时候用html_message
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用美多商城。</p>' \
                       '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                       '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)

        from celery_tasks.email.tasks import celery_send_mail
        celery_send_mail.delay(subject=subject,
                               message=message,
                               from_email=from_email,
                               recipient_list=recipient_list,
                               html_message=html_message)

        # 5.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


class EmailVerifyView(View):

    def put(self, request):
        # 1.接受请求,获取参数
        token = request.GET.get('token')
        # 2.验证参数
        if token is None:
            return JsonResponse({'code': 400, 'errmsg': '参数缺失'})

        # 3.获取user_id
        from apps.users.utils import check_email_verify_token
        user_id = check_email_verify_token(token)
        if user_id is None:
            return JsonResponse({'code': 400, 'errmsg': '参数错误'})

        # 4.根据user_id查询数据,修改数据
        user = User.objects.get(id=user_id)
        user.email_active = True
        user.save()

        # 5.返回相应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


class CreateAddressView(LoginRequiredJSONMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode())
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        user = request.user

        # 验证参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400, 'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        # 数据入库
        address = Address.objects.create(
            user=user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})


class AddressView(LoginRequiredJSONMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供地址管理界面
        """
        # 获取所有的地址:
        addresses = Address.objects.filter(user=request.user, is_deleted=False)
        # 创建空的列表
        address_list = []
        # 遍历
        for address in addresses:
            address_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        # 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'addresses': address_list})


class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400, 'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            # logger.error(e)
            return JsonResponse({'code': 400, 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return JsonResponse({'code': 0, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)
            # 逻辑删除
            address.is_deleted = True
            address.save()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '删除地址失败'})

        return JsonResponse({'code': 0, 'errmsg': '删除地址成功'})
