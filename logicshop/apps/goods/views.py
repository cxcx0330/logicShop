from django import http
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View

from contents.utils import get_categories
from utils.response_code import RETCODE
from . import constants
from .models import GoodsCategory, SKU
from .utils import get_breadcrumb


# Create your views here.

class HotGoodsView(View):
    """热销排行"""

    def get(self, request, category_id):
        # 查询指定分类，必须上架商品，按照销量排序，取前两个 直接切片取前两个
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        # 模型转字典列表
        # 需要将全部数据添加到列表中，
        hot_skus = []
        for sku in skus:
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url,
            }
            hot_skus.append(sku_dict)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class GoodsListView(View):
    """商品的列表页面"""

    def get(self, request, category_id, page_num):
        # category_id 参数校验
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            # 返回403
            return http.HttpResponseForbidden('参数category不存在')
        # 获取sort排序参数从路径中 default默认值 未传入sort参数使用默认值default
        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            sort_filed = 'price'
        elif sort == 'hot':
            sort_filed = 'sales'
        else:
            sort = 'default'
            sort_filed = 'create_time'
        # 分页与排序
        # 排序
        skus = SKU.objects.filter(is_launched=True, category_id=category.id).order_by(sort_filed)
        # 分页 将排序好的数据进行分页，所有数据，每页的数据量
        paginator = Paginator(skus, constants.EVERY_PAGE_NUMBER)
        # 获取当前页面的数据
        try:
            page_skus = paginator.page(page_num)
        except Exception as e:
            return http.HttpResponseNotFound('Empty Page')
        # print(page_skus)
        # 总页数
        total_page = paginator.num_pages

        # 　查询商品分类
        categories = get_categories()
        # 　查询并完成面包屑
        # 使用封装的思想，需要传入参数category
        breadcrumb = get_breadcrumb(category)
        # category_id 3级
        # breadcrumb = {
        #     'cat1': category.parent.parent,
        #     'cat2': category.parent,
        #     'cat3': category,
        # }
        # print(breadcrumb)
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'page_skus': page_skus,
            'total_page': total_page,
            'sort': sort,
            'category_id': category_id,
            'page_num': page_num,

        }
        return render(request, 'list.html', context=context)
