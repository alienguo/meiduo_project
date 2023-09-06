from django.shortcuts import render

# Create your views here.

# from fdfs_client.client import Fdfs_client
#
# # 1.创建客户端
# # 修改加载配置文件的路径
# client = Fdfs_client('utils/fastdfs/client.conf')
# # 2.上传图片
# client.upload_by_filename('D:/BrowserDownload/1.jpg')

# 获取file_id
"""
{'Group name': 'group1', 'Remote file_id': 'group1\\M00/00/00/wKghgGT2ny6AD382AAF2RDc3rdA365.jpg', 
'Status': 'Upload successed.', 'Local file name': 'D:/BrowserDownload/1.jpg', 'Uploaded size': '93.00KB', 
'Storage IP': '192.168.33.128'}
"""
from django.views import View
from utils.goods import get_categories, get_goods_specs
from apps.contents.models import ContentCategory


class IndexView(View):

    def get(self, request):

        # 商品分类数据
        categories = get_categories()
        # 广告数据
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 渲染模板的上下文
        context = {
            'categories': categories,
            'contents': contents,
        }
        return render(request, 'index.html', context)


from apps.goods.models import GoodsCategory, SKU
from django.http import JsonResponse
from utils.goods import get_breadcrumb
from django.core.paginator import Paginator
class ListView(View):

    def get(self, request, category_id):
        # 1.接收参数
        # 排序字段
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')

        # 2.获取分类id

        # 3.根据分类id进行分类数据的查询验证
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数缺失'})

        # 4.获取面包屑数据
        breadcrumb = get_breadcrumb(category)
        # 5.查询分类对应的sku数据，然后排序，然后分页
        try:
            skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '获取mysql数据出错'})

        paginator = Paginator(skus, page_size)
        # 获取每页商品数据
        page_skus = paginator.page(page)
        # 获取列表页总页数
        total_page = paginator.num_pages

        # 定义列表:
        list = []
        # 整理格式:
        for sku in page_skus:
            list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        # 把数据变为 json 发送给前端
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'list': list,
            'count': total_page
        })


class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行JSON数据"""
        # 根据销量倒序
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        # 序列化
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        return JsonResponse({'code': 0, 'errmsg': 'OK', 'hot_skus': hot_skus})

# 导入:
from haystack.views import SearchView


class SKUSearchView(SearchView):
    """重写SearchView类"""
    def create_response(self):
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })
        # 拼接参数, 返回
        return JsonResponse(data_list, safe=False)


"""
需求：
    详情页面
    
    1.分类数据
    2.面包屑
    3.SKU信息
    4.规格信息
"""

class DetailView(View):

    def get(self, request, sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            # return render(request, '404.html')
            pass
        # 1.分类数据
        categories = get_categories()
        # 2.面包屑
        breadcrumb = get_breadcrumb(sku.category)
        # 3.SKU信息
        # 4.规格信息
        goods_space = get_goods_specs(sku)

        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
        }
        return render(request, 'detail.html', context)
