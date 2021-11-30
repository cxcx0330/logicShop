import base64
import json
import pickle

from django import http
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from goods.models import SKU
from utils.response_code import RETCODE


# Create your views here.
class CartsSelectAllView(View):
    """全选购物车"""

    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        # 接收selected参数
        selected = json_dict.get('selected')

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected错误')

        user = request.user
        # 判断是否登录
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')

            # 获取所有的记录  {b'3': b'1', b'4': '2'}
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)

            # 取出keys 3 4
            redis_sku_ids = redis_cart.keys()

            if selected:
                # for redis_sku_id in redis_sku_ids:
                #     redis_conn.sadd('selected_%s' % user.id, redis_sku_id)
                redis_conn.sadd('selected_%s' % user.id, *redis_sku_ids)
            else:
                for redis_sku_id in redis_sku_ids:
                    redis_conn.srem('selected_%s' % user.id, redis_sku_id)

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        else:
            # 　用户未登录
            cart_str = request.COOKIES.get('carts')

            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
            # 将空字典加密后的值进行排除
            if cart_str and cart_str != 'gAN9cQAu':
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)

                # cart_dict = {'1': {'count': 10, 'selected': True}, '2': {'count': 20, 'selected': False}}

                # 修改字典中的selected字段的值
                for sku_id in cart_dict:
                    cart_dict[sku_id]['selected'] = selected
                # 重写数据 加密数据
                cart_dict_bytes = pickle.dumps(cart_dict)

                cart_str_bytes = base64.b64encode(cart_dict_bytes)

                cookie_cart_str = cart_str_bytes.decode()

                # 将新的购物车数据写入到cookie中

                response.set_cookie('carts', cookie_cart_str)

            return response


class CartsView(View):
    """购物车管理"""

    def get(self, request):

        user = request.user
        if user.is_authenticated:
            # 用户已经登录
            redis_conn = get_redis_connection('carts')

            #  字节类型 {b'3': b'1', b'4': b'2'} 3号商品 1件
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            # 字节类型 {b'3', b'4'} 3 4 商品被选中
            redis_selected = redis_conn.smembers('selected_%s' % user.id)
            """
            {
                "sku_id1":{
                    "count":"1",
                    "selected":"True"
                },
                "sku_id3":{
                    "count":"3",
                    "selected":"True"
                }
            }
            """
            # 将redis中取出的数据格式调整的与cookies中的数据格式相同
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                # 将字节直接转换成整形
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected
                }
        else:
            # 用户未登陆
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

        # {3: {'count': 2, 'selected': True}, 5: {'count': 2, 'selected': True}}

        # 将页面需要的数据从数据库中查询出来，返回给页面
        sku_ids = cart_dict.keys()
        # for sku_id in sku_ids:
        #     sku = SKU.objects.get(id=sku_id)
        # 使用模型的过滤条件，然后在使用循环
        skus = SKU.objects.filter(id__in=sku_ids)

        # 循环查询出来的对象集合
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': str(cart_dict.get(sku.id).get('selected')),  # True => 'True'
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'amount': str(sku.price * cart_dict.get(sku.id).get('count'))
            })

        context = {
            'cart_skus': cart_skus
        }
        return render(request, 'cart.html', context=context)

    def post(self, request):
        """
        1.接收参数
        2.校验参数
        3.判断用户是否登录
        4.用户已经登录,操作Redis购物车
        5.用户未登陆,操作cookie购物车
        6.响应结果
        """
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)  # 可选参数

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')

        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('参数count错误')

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected错误')

        user = request.user
        if user.is_authenticated:
            # 用户已经登录
            redis_conn = get_redis_connection('carts')
            # carts_user_id: {sku_id1: count, sku_id3: count, sku_id5: count, ...}
            # 需要以增量计算的形式保存商品数据
            shop = redis_conn.hget('cart_%s' % user.id, sku_id)
            pl = redis_conn.pipeline()
            # if shop:
            #     count = int(shop) + count
            #     redis_conn.hset('cart_%s' % user.id, sku_id, count)
            # else:
            #     redis_conn.hset('cart_%s' % user.id, sku_id, count)
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)

            # 执行
            pl.execute()

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        else:
            # 用户未登陆
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            # cart_dict = {'1': {'count': 10, 'selected': True}, '2': {'count': 20, 'selected': False}}
            if sku_id in cart_dict:
                # 购物车已经存在 增量计算
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # else:
            #     # 创建一个
            #     cart_dict[sku_id] = {
            #         'count': count,
            #         'selected': selected
            #     }

            cart_dict_bytes = pickle.dumps(cart_dict)

            cart_str_bytes = base64.b64encode(cart_dict_bytes)

            cookie_cart_str = cart_str_bytes.decode()

            # 将新的购物车数据写入到cookie中
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

            response.set_cookie('carts', cookie_cart_str)

            return response

    def put(self, request):
        """购物车的修改"""
        # 　从request body中接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)  # 可选参数

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')

        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('参数count错误')

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected错误')

        user = request.user
        # 使用django的用户验证进行判断
        if user.is_authenticated:
            # 用户已经登录
            redis_conn = get_redis_connection('carts')
            # 管道
            pl = redis_conn.pipeline()

            # 操作hash  覆盖写入的方式
            pl.hset('cart_%s' % user.id, sku_id, count)

            # 操作set
            if selected:
                # 选中进行添加
                # 将选中的商品进行合并
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                # 没有选中则将数据删除
                pl.srem('selected_%s' % user.id, sku_id)

            # 执行
            pl.execute()
            # 将数据返回给页面
            cart_sku = {
                'id': sku_id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price,
                'count': count,
                'amount': sku.price * count,
                'selected': selected
            }
            # 响应结果 Ajax请求
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})

        else:
            # 用户未登陆
            # 获取cookies
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            # {3: {'count': 2, 'selected': True}, 5: {'count': 2, 'selected': True}}
            # 将数据覆盖写入 而不是创建新的字典 避免将未进行修改的数据消除掉
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cart_sku = {
                'id': sku_id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price,
                'count': count,
                'amount': sku.price * count,
                'selected': selected
            }
            cart_dict_bytes = pickle.dumps(cart_dict)

            cart_str_bytes = base64.b64encode(cart_dict_bytes)

            cookie_cart_str = cart_str_bytes.decode()
            # 重新写入到cookie中
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
            response.set_cookie('carts', cookie_cart_str)

            # 响应结果
            return response

    def delete(self, request):
        """删除购物车"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')

        user = request.user
        if user.is_authenticated:
            # 用户登录
            redis_conn = get_redis_connection('carts')
            # 使用管道
            pl = redis_conn.pipeline()
            # 删除关于sku_id的数据
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        else:
            # 用户未登陆
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 转成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 转成bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转成真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            # sku_id:3
            # {3: {'count': 2, 'selected': True}, 5: {'count': 2, 'selected': True}}
            # 要删除的sku_id不存在直接返回response

            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

            if sku_id in cart_dict:
                # 删除数据 del['sku_id']
                del cart_dict[sku_id]

                cart_dict_bytes = pickle.dumps(cart_dict)

                cart_str_bytes = base64.b64encode(cart_dict_bytes)

                cookie_cart_str = cart_str_bytes.decode()

                # 重新写入到cookie中
                # 　数据存在，修改cookie中的数据
                response.set_cookie('carts', cookie_cart_str)

                # 响应结果
            return response
