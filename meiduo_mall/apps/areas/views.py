from django.shortcuts import render

# Create your views here.
from django.views import View
from apps.areas.models import Area
from django.http import JsonResponse
from django.core.cache import cache


class AreaView(View):

    def get(self, request):

        # 先查询缓存数据
        province_list = cache.get('province')

        if province_list is None:
            # 1.查询省份信息
            provinces = Area.objects.filter(parent=None)   # 查询结果集
            # 将对象转化为字典数据
            province_list = []
            for province in provinces:
                province_list.append({
                    'id': province.id,
                    'name': province.name
                })

            # 保存缓存数据
            cache.set('province', province_list, 24*3600)

        # 2.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'province_list': province_list})


class SubAreaView(View):

    def get(self, request, id):

        # 先查询缓存数据
        sub_data = cache.get('city:%s' % id)

        if sub_data is None:
            up_level = Area.objects.get(id=id)
            low_level = up_level.subs.all()

            sub_data = []
            for item in low_level:
                sub_data.append({
                    'id': item.id,
                    'name': item.name
                })

            # 保存缓存数据
            cache.set('city:%s' % id, sub_data, 24 * 3600)

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'sub_data': {'subs': sub_data}})

