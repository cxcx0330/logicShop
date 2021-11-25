from django.shortcuts import render
from django.views import View

from .models import ContentCategory, Content
from .utils import get_categories


# Create your views here.

class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页页面"""
        # 查询并展示商品分类
        categories = get_categories()
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
