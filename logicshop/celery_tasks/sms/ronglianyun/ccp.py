import json

from ronglian_sms_sdk import SmsSDK

accId = '8a216da875e463e00175ef36a22902ee'
accToken = 'a550937adda0404385808ab276af2f2f'
appId = '8aaf07087ce03b67017d08e024d10905'


# 单例设计  模式
class CCP(object):
    def __new__(cls, *args, **kwargs):
        # 第一次实例化，则返回实例对象
        # 判断是否存在类属性，_instance
        if not hasattr(cls, '_instance'):
            # cls._instance ==> CCP实例
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            # CCP().sdk 给对象动态添加属性
            cls._instance.sdk = SmsSDK(accId, accToken, appId)
        # 如果存在则直接返回
        return cls._instance

    def send_message(self, mobile, datas, tid):
        # 已经添加好的属性，直接使用
        sdk = self._instance.sdk
        # tid = '1'
        # mobile = '17764713162'
        # datas = ('1234', '5')
        resp = sdk.sendMessage(tid, mobile, datas)
        # print(resp)
        result = json.loads(resp)
        if result['statusCode'] == '000000':
            return 0
        else:
            return -1


if __name__ == '__main__':
    c = CCP()
    c.send_message('17764713162', ('5555', '5'), '1')
    # c = CCP()
    # print(id(c))
    # c1 = CCP()
    # print(id(c1))
    # c2 = CCP()
    # print(id(c2))
