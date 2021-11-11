import random

from django import http
from django.views import View
from django_redis import get_redis_connection

from utils.response_code import RETCODE
from . import constants
from .libs.captcha.captcha import captcha
from .libs.ronglianyun.ccp import CCP


# Create your views here.

class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        """

        :param request: 接收路径中校验过后的参数 re_path
        :param uuid: 通用唯一识别符，用于区别图片验证码属于哪个用户
        :return:图片image/jpg
        """
        # 生成图片验证码
        text, image = captcha.generate_captcha()
        # print(text,image)
        # 保存图片验证码到redis中 链接验证码redis库
        # 1.建立redis链接
        redis_conn = get_redis_connection(alias='verify_code')
        # 2.保存数据 name time value
        redis_conn.setex(f'img_{uuid}', constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 响应图形验证码（将图片返回给前端） 返回值为图片验证码
        return http.HttpResponse(image, content_type='image/png')


class SMSCodeView(View):
    """短信验证码"""

    def get(self, request, mobile):
        """

        :param request:
        :param mobile: 手机号
        :return:json
        """
        # 接收参数，校验参数
        uuid = request.GET.get('uuid')
        image_code_client = request.GET.get('image_code')
        if not all([uuid, image_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 提取图形验证码
        redis_conn = get_redis_connection('verify_code')
        # 判断用户是否频繁发送短信验证码
        send_flag = redis_conn.get(f'send_flag_{mobile}')
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        image_code_server = redis_conn.get(f'img_{uuid}')
        # 提取图形验证码失效
        if image_code_server is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})
        # 删除图形验证码
        redis_conn.delete(f'img_{uuid}')
        # 对比图形验证码
        # image_code_server 字节  image_code_client 字符串 需要解码 然后统一转换成小写
        image_code_server = image_code_server.decode()
        if image_code_server.lower() != image_code_client.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入图形验证码有误'})
        # 生成短信验证码
        # 生成6位随机数

        sms_code = '%06d' % random.randint(0, 999999)
        # # 保存短信验证码
        # redis_conn.setex(f'sms_{mobile}', constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # # 保存发送短信验证码的标记
        # redis_conn.setex(f'send_flag_{mobile}', constants.SEND_SMS_CODE_TIMES, 1)

        # 　创建redis管道
        pl = redis_conn.pipeline()
        # 　将命令添加到队列中
        # 保存短信验证码
        pl.setex(f'sms_{mobile}', constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送短信验证码的标记
        pl.setex(f'send_flag_{mobile}', constants.SEND_SMS_CODE_TIMES, 1)
        # 执行管道中的命令
        pl.execute()


        # 发送短信 实例化调用方法  都是字符串数据类型 300/60 float 300//60 int
        CCP().send_message(str(mobile), (str(sms_code), str(constants.SMS_CODE_REDIS_EXPIRES // 60)),
                           constants.SEND_SMS_TEMPLATE_TD)
        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信验证码成功'})
