# @Time: 2021/11/23-15:48
# @User: Ycx
from .models import GoodsCategory


def get_breadcrumb(category):
    """
    查询面包屑
    :param category:类别，从数据库查询出来的，作为参数传递
    :return:
    """
    breadcrumb = {
        'cat1': '',
        'cat2': '',
        'cat3': '',
    }
    # 一级
    if category.parent is None:
        breadcrumb['cat1'] = category
    # 3级
    elif GoodsCategory.objects.filter(parent_id=category.id).count() == 0:
        cat2 = category.parent
        breadcrumb['cat1'] = cat2.parent
        breadcrumb['cat2'] = cat2
        breadcrumb['cat3'] = category
    # 2级
    else:
        breadcrumb['cat1'] = category.parent
        breadcrumb['cat2'] = category
    return breadcrumb
