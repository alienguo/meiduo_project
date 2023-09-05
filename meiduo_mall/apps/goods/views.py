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
from utils.goods import get_categories
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
