from django import http
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from contents.utils import get_categories
from utils.response_code import RETCODE
from . import constants
from .models import GoodsCategory, SKU, SKUSpecification, SPUSpecification, GoodsVisitCount
from .utils import get_breadcrumb


# Create your views here.


class DetailVisitView(View):
    """详情页分类商品访问量"""

    def post(self, request, category_id):
        """记录分类商品访问量"""
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('缺少必传参数')
        # 获取今天的日期
        t = timezone.localtime()
        today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)
        try:
            # 存在记录 修改记录
            counts_data = GoodsVisitCount.objects.get(date=today_str, category=category.id)
            # 不存在记录新增

        except Exception as e:
            counts_data = GoodsVisitCount()
        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.date = today_str
            counts_data.save()
        except Exception as e:
            return http.HttpResponseForbidden('统计失败')

        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DetailGoodsView(View):
    """商品的详情页面"""

    def get(self, request, sku_id):
        # 校验参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return render(request, '404.html')
        # 　查询商品分类
        categories = get_categories()
        # 　查询并完成面包屑
        # 使用封装的思想，需要传入参数category
        breadcrumb = get_breadcrumb(sku.category)
        # 第一次进入详情页面使用默认值
        # 构建当前商品的规格键 当前的默认规格
        sku_specs = SKUSpecification.objects.filter(sku__id=sku_id).order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)

        # 获取当前商品的所有SKU
        spu_id = sku.spu_id
        skus = SKU.objects.filter(spu_id=spu_id)

        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id

        # 获取当前商品的规格信息
        goods_specs = SPUSpecification.objects.filter(spu_id=spu_id).order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs
        }
        return render(request, 'detail.html', context=context)


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
