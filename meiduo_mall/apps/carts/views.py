import json
import pickle
import base64
from django.views import View
from apps.goods.models import SKU
from django.http import JsonResponse
from django.shortcuts import render
from django_redis import get_redis_connection


class CartsView(View):
    """购物车管理"""
    def post(self, request):
        # 1.接收数据
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        # 2.验证数据
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '查无此商品'})

        # 判断count是否为数字
        try:
            count = int(count)
        except Exception:
            count = 1
        # 3.判断用户的登录状态
        user = request.user
        if user.is_authenticated:
            # 4.登录用户保存redis
            #   4.1 链接redis
            redis_cli = get_redis_connection('carts')
            #   4.2 操作hash
            redis_cli.hset('carts_%s' % user.id, sku_id, count)
            #   4.3 操作set
            # 默认选中
            redis_cli.sadd('selected_%s' % user.id, sku_id)
            #   4.4 返回响应
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            # 5.未登录用户保存cookie
            #   5.0 先获取cookie数据
            cookie_carts = request.COOKIES.get('carts')
            if cookie_carts:
                carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                #   5.1 创建cookie字典
                carts = {}
            # 判断新增的商品有没有在购物车里
            if sku_id in carts:
                # 购物车中已有商品id, 数量累加
                origin_count = carts[sku_id]['count']
                count += origin_count

            carts[sku_id] = {
                'count': count,
                'selected': True
            }
            #   5.2 字典转为bytes
            carts_bytes = pickle.dumps(carts)
            #   5.3 bytes类型数据base64编码
            base64encode = base64.b64encode(carts_bytes)
            #   5.4 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts', base64encode.decode(), max_age=3600*24*12)
            #   5.5 返回响应
            return response

    def get(self, request):
        # 1.判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 2.登录用户查询redis
            redis_cli = get_redis_connection('carts')
            sku_id_count = redis_cli.hgetall('carts_%s' % user.id)
            selected_ids = redis_cli.smembers('selected_%s' % user.id)
            carts = {}
            for sku_id, count in sku_id_count.items():
                carts[sku_id] = {
                    'count': count,
                    'selected': sku_id in selected_ids
                }
        else:
            # 3.未登录用户查询cookie
            carts = request.COOKIES.get('carts')
            cookie_carts = request.COOKIES.get('carts')
            if cookie_carts:
                carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                carts = {}

        # 4.根据商品id查询商品信息
        sku_ids = carts.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        # 5.将对象数据转化为字典数据
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts.get(sku.id).get('count'),
                'selected': str(carts.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts.get(sku.id).get('count'))
            })
        # 6.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'cart_skus': cart_skus})

    def put(self, request):
        user = request.user
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected')

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '没有此商品'})

        try:
            count = int(count)
        except Exception:
            count = 1

        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            redis_cli.hest('carts_%s' % user.id, sku_id, count)
            if selected:
                redis_cli.sadd('selected_%s' % user.id, sku_id)
            else:
                redis_cli.srem('selected_%s' % user.id, sku_id)
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': {'count': count, 'selected': selected}})
        else:
            cookie_carts = request.COOKIES.get('carts')
            if cookie_carts:
                carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                carts = {}
            if sku_id in carts:
                carts[sku_id] = {
                    'count': count,
                    'selected': selected
                }
            new_carts = base64.b64encode(pickle.dumps(carts))
            response = JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': {'count': count, 'selected': selected}})
            response.set_cookie('carts', new_carts.decode(), max_age=3600*24*14)
            return response
