# Create your views here.
from django import http
from django.core.cache import cache
from django.views import View

from utils.response_code import RETCODE
from .models import Area


class AreasView(View):
    """省市区的三级联动"""

    def get(self, request):
        # 接受参数
        # area_id 判断当前是要查询省份数据还是市区数据
        area_id = request.GET.get('area_id')

        if not area_id:
            # 首先再缓存中查询
            province_list = cache.get('province_list')
            if not province_list:
                # 查询省份数据  parent_id  is null
                try:
                    province_model_list = Area.objects.filter(parent__isnull=True)
                    province_list = []
                    for province_model in province_model_list:
                        province_dict = {
                            'id': province_model.id,
                            'name': province_model.name,
                        }
                        province_list.append(province_dict)
                    # 将数据缓存到redis中
                    cache.set('province_list', province_list, 3600)
                    # return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
                except Exception as e:
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询省份数据错误'})
            # else:
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})



        else:
            sub_data = cache.get('sub_area_' + area_id)
            if not sub_data:
                try:
                    # 查询市区数据
                    # 一查多数据
                    # parent_model=Area.objects.filter(parend_id=area_id)
                    parent_model = Area.objects.get(id=area_id)
                    sub_model_list = parent_model.subs.all()
                    """
                                    {
                          "code":"0",
                          "errmsg":"OK",
                          "sub_data":{
                              "id":130000,
                              "name":"河北省",
                              "subs":[
                                  {
                                      "id":130100,
                                      "name":"石家庄市"
                                  },
                              ]
                          }
                        }
                    """
                    subs = []
                    for sub_model in sub_model_list:
                        sub_dict = {
                            'id': sub_model.id,
                            'name': sub_model.name
                        }
                        subs.append(sub_dict)

                    sub_data = {
                        'id': parent_model.id,
                        'name': parent_model.name,
                        'subs': subs,
                    }
                    cache.set('sub_area_' + area_id, sub_data, 3600)
                except Exception as e:
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询数据错误'})

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})
