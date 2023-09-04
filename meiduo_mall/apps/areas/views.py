from django.shortcuts import render

# Create your views here.
from django.views import View
from apps.areas.models import Area
from django.http import JsonResponse


class AreaView(View):

    def get(self, request):
        # 1.查询省份信息
        provinces = Area.objects.filter(parent=None)   # 查询结果集
        # 将对象转化为字典数据
        province_list = []
        for province in provinces:
            province_list.append({
                'id': province.id,
                'name': province.name
            })
        # 2.返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'province_list': province_list})


class SubAreaView(View):

    def get(self, request, id):
        up_level = Area.objects.get(id=id)
        low_level = up_level.subs.all()

        sub_data = []
        for item in low_level:
            sub_data.append({
                'id': item.id,
                'name': item.name
            })

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'sub_data': {'subs': sub_data}})

