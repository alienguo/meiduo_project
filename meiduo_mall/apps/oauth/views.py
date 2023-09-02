from django.shortcuts import render

# Create your views here.


"""
1. QQ互联开发平台申请成为开发者（可以不用做）
2. QQ互联创建应用（可以不用做）
3. 按照文档开发（看文档的）
3.1 准备工作                        -----------------------------------准备好了
    # QQ登录参数
    # 我们申请的 客户端id
    QQ_CLIENT_ID = '101474184'          appid
    # 我们申请的 客户端秘钥
    QQ_CLIENT_SECRET = 'c6ce949e04e12ecc909ae6a8b09b637c'   appkey
    # 我们申请时添加的: 登录成功后回调的路径
    QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'
3.2 放置 QQ登录的图标（目的： 让我们点击QQ图标来实现第三方登录）  ------------- 前端做好了
3.3 根据oauth2.0 来获取code 和 token                      ---------------我们要做的
    对于应用而言，需要进行两步：
    1. 获取Authorization Code；            表面是一个链接，实质是需要用户同意，然后获取code
    2. 通过Authorization Code获取Access Token
3.4 通过token换取 openid                                ----------------我们要做的
    openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份，
    或将其与用户在网站上的原有账号进行绑定。
把openid 和 用户信息 进行一一对应的绑定

生成用户绑定链接 ---------->获取code ----------->获取token ------------>获取openid -------->保存openid


前端： 当用户点击QQ登录图标的用户，前端发送一个axios(Ajax)请求
后端：
    请求
    业务逻辑：调用QQLoginTool 生成跳转链接
    响应      返回跳转链接
    路由      GET qq/authorization/ 
"""
from django.views import View
from django.http import JsonResponse
from apps.oauth.models import OAuthQQUser
from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from meiduo_mall.settings import QQ_CLIENT_ID, QQ_CLIENT_SECRET, QQ_REDIRECT_URI


class QQLoginURLView(View):

    def get(self, request):
        # 1.QQLoginTool实例对象
        # client_id   appid
        # client_secret  appkey
        # redirect_uri   用户同意登录后跳转的页面
        # state
        qq = OAuthQQ(client_id=QQ_CLIENT_ID,
                     client_secret=QQ_CLIENT_SECRET,
                     redirect_uri=QQ_REDIRECT_URI,
                     state='xxxx')

        # 2.调用对象方法生成跳转链接
        qq_login_url = qq.get_qq_url()

        # 3.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'login_url': qq_login_url})


"""
后端
    业务逻辑：获取code(前端发送的请求) ---->获取token --->获取openid ---> 根据openid进行判断是否需要进行绑定
    路由：GET  oauth_callback/?code=xxxxx
"""


class OauthQQView(View):

    def get(self, request):
        # 1.获取code
        code = request.GET.get('code')
        if code is None:
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 2.通过code换取token
        qq = OAuthQQ(client_id=QQ_CLIENT_ID,
                     client_secret=QQ_CLIENT_SECRET,
                     redirect_uri=QQ_REDIRECT_URI,
                     state='xxxx')
        token = qq.get_access_token(code)

        # 3.再通过token获取openid
        openid = qq.get_open_id(token)

        # 4. 根据openid查询判断
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 不存在，需要绑定
            response = JsonResponse({'code': 400, 'access_token': openid})
            return response
        else:
            # 存在 则绑定过，直接登录
            login(request, qquser.user)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('username', qquser.user.username)

            return response
