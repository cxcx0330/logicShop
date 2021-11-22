from collections import OrderedDict

from django.shortcuts import render
from django.views import View

from goods.models import GoodsChannel, GoodsCategory
from .models import ContentCategory, Content


# Create your views here.

class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页页面"""
        # 查询并展示商品分类
        categories = OrderedDict()
        # 查询所有频道数据
        # 　按照组id查询，再按照商品顺序查询
        channels = GoodsChannel.objects.order_by('group_id', 'sequence')
        # 查询一级类别
        for channel in channels:
            # 　37频道 11组
            group_id = channel.group_id
            if group_id not in categories:
                categories[group_id] = {'channels': [], 'sub_cats': []}

            # 利用django模型中定义的字段可以得到category整个对象(全部数据)
            cat1 = channel.category
            categories[group_id]['channels'].append(
                {
                    'id': cat1.id,
                    'name': cat1.name,
                    'url': channel.url,
                })
            # 查询二级类别
            for cat2 in GoodsCategory.objects.filter(parent_id=cat1.id).all():
                # 给对象新建属性为列表：
                cat2.sub_cats = []
                categories[group_id]['sub_cats'].append(
                    {
                        'id': cat2.id,
                        'name': cat2.name,
                        # 三级类别
                        'sub_cats': cat2.sub_cats,
                    }
                )
                # 查询三级类别
                for cat3 in GoodsCategory.objects.filter(parent_id=cat2.id).all():
                    # 　给对象中的列表添加值
                    cat2.sub_cats.append({
                        'id': cat3.id,
                        'name': cat3.name,
                    })
        # 查询首页所有的广告
        # 　1.查询所有的广告类别
        context_categories = ContentCategory.objects.all()
        contents = {}
        for context_category in context_categories:
            contents[context_category.key] = Content.objects.filter(category_id=context_category.id,
                                                                    status=True).all().order_by('sequence')
        # print(categories)
        # print(contents)
        context = {
            'categories': categories,
            'contents': contents
        }
        return render(request, 'index.html', context=context)
