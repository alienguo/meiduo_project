import pickle
import base64

from django_redis import get_redis_connection


def merge_cookie_to_redis(request, response):
    # 1.读取cookie数据
    cookie_carts = request.COOKIES.get('carts')
    if cookie_carts is not None:
        carts = pickle.loads(base64.b64decode(cookie_carts))
        # 2.初始化一个字典 用于保存sku_id:count
        cookie_dict = {}
        #     初始化一个列表， 用于保存选中的商品
        selected_ids = []
        #     初始化一个列表 用于保存未选中的商品
        unselected_ids = []
        # 3.遍历cookie数据
        for sku_id, count_selected_dict in carts.items():
            cookie_dict[sku_id] = count_selected_dict['count']
            if count_selected_dict['selected']:
                selected_ids.append(sku_id)
            else:
                unselected_ids.append(sku_id)
        user = request.user
        # 4.将字典数据、列表数据分别添加到redis中
        redis_cli = get_redis_connection('carts')
        pipeline = redis_cli.pipeline()
        pipeline.hmset('carts_%s' % user.id, cookie_dict)
        if len(selected_ids) > 0:
            pipeline.sadd('selected_%s' % user.id, *selected_ids)   # * 对列表数据进行解包
        if len(unselected_ids) > 0:
            pipeline.srem('selected_%s' % user.id, *unselected_ids)

        pipeline.execute()
        # 5.删除cookie数据
        response.delete_cookie('carts')

    return response
