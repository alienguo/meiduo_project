import json
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from decimal import Decimal
from django.views import View
from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
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


class OrderCommitView(LoginRequiredJSONMixin, View):
    """订单提交"""

    def post(self, request):
        """保存订单信息和订单商品信息"""
        # 获取当前要保存的订单数据
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        # 校验参数
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数}'})
        # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception:
            return JsonResponse({'code': 400, 'errmsg': '参数address_id错误'})
        # 判断pay_method是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': 400, 'errmsg': '参数pay_method错误'})

        # 获取登录用户
        user = request.user
        # 生成订单编号：年月日时分秒+用户编号
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 显式的开启一个事务
        with transaction.atomic():
            # 创建事务保存点
            save_id = transaction.savepoint()

            # 暴力回滚
            try:
                # 保存订单基本信息 OrderInfo（一）
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                # 从redis读取购物车中被勾选的商品信息
                redis_conn = get_redis_connection('carts')
                redis_cart = redis_conn.hgetall('carts_%s' % user.id)
                selected = redis_conn.smembers('selected_%s' % user.id)
                carts = {}
                for sku_id in selected:
                    carts[int(sku_id)] = int(redis_cart[sku_id])
                sku_ids = carts.keys()

                # 遍历购物车中被勾选的商品信息
                for sku_id in sku_ids:
                    while True:
                        # 查询SKU信息
                        sku = SKU.objects.get(id=sku_id)

                        # 读取原始库存
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        # 判断SKU库存
                        sku_count = carts[sku.id]
                        if sku_count > origin_stock:
                            # 事务回滚
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'code': 400, 'errmsg': '库存不足'})

                        # 模拟延迟
                        # import time
                        # time.sleep(5)

                        # SKU减少库存，增加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # 乐观锁更新库存和销量
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)
                        # 如果下单失败，但是库存足够时，继续下单，直到下单成功或者库存不足为止
                        if result == 0:
                            continue

                        # 保存订单商品信息 OrderGoods（多）
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        # 保存商品订单中总价和总数量
                        order.total_count += sku_count
                        order.total_amount += (sku_count * sku.price)

                        # 下单成功或者失败就跳出循环
                        break

                # 添加邮费和保存订单信息
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                # 事务回滚
                transaction.savepoint_rollback(save_id)
                return JsonResponse({'code': 400, 'errmsg': '下单失败'})

        # 保存订单数据成功，显式的提交一次事务
        transaction.savepoint_commit(save_id)

        # 清除购物车中已结算的商品
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *selected)
        pl.srem('selected_%s' % user.id, *selected)
        pl.execute()

        # 响应提交订单结果
        return JsonResponse({'code': 0, 'errmsg': '下单成功', 'order_id': order.order_id})
