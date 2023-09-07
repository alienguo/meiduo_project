from django.http import JsonResponse
from django.shortcuts import render
from decimal import Decimal
from django.views import View
from apps.goods.models import SKU
from apps.users.models import Address
from utils.views import LoginRequiredJSONMixin
from django_redis import get_redis_connection


class OrderSettlementView(LoginRequiredJSONMixin, View):
    """结算订单"""
    def get(self, request):
        # 1.获取用户信息
        user = request.user
        # 2.地址信息
        #   2.1 查询用户地址信息
        addresses = Address.objects.filter(is_deleted=False)
        #   2.2 将对象数据转换为字典数据
        address_list = []
        for address in addresses:
            address_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })

        # 3.购物车中选中商品信息
        redis_cli = get_redis_connection('carts')
        # redis_cli.hgetall('carts_%s' % user.id)
        # redis_cli.smembers('selected_%s' % user.id)
        pipeline = redis_cli.pipeline()
        pipeline.hgetall('carts_%s' % user.id)
        pipeline.smembers('selected_%s' % user.id)
        result = pipeline.execute()
        sku_id_count = result[0]
        selected_ids = result[1]

        selected_cart = {}
        for sku_id in selected_ids:
            selected_cart[int(sku_id)] = int(sku_id_count[sku_id])

        # 查询商品信息
        sku_list = []
        # 查询商品信息
        skus = SKU.objects.filter(id__in=selected_cart.keys())
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'count': selected_cart[sku.id],
                'price': sku.price
            })

        freight = Decimal('10.00')
        # 渲染界面
        context = {
            'addresses': address_list,
            'skus': sku_list,
            'freight': freight,
        }

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'context': context})



