# 创建任务 发送短信
from celery_tasks.main import celery_app
from celery_tasks.sms.ronglianyun.ccp import CCP
from . import constants


# name 给任务取名字
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    发送短信验证码的异步任务
    :param mobile:手机号
    :param sms_code:短信验证
    :return:成功 0 失败 -1
    """
    # 发送短信 实例化调用方法  都是字符串数据类型 300/60 float 300//60 int
    send_ret = CCP().send_message(str(mobile), (str(sms_code), str(constants.SMS_CODE_REDIS_EXPIRES // 60)),
                                  constants.SEND_SMS_TEMPLATE_TD)
    return send_ret
