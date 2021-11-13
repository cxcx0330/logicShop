from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from . import constants


# 加密
def generate_access_token(openid):
    """
    签名、序列化openid
    :param openid: qq用户的明文id
    :return:密文
    """
    # SECRET_KEY django 配置文件dev中自带密钥
    serializer = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)
    # 需要加密的数据 字典形式
    data = {'openid': openid}
    # 进行加密 类型：字节
    token = serializer.dumps(data)
    # 返回值为openid的密文
    return token.decode()


# 解密
def check_access_token(openid):
    """
    反序列化
    :param openid: openid的密文
    :return:明文
    """
    # 创建对象
    serializer = Serializer(settings.SECRET_KEY, constants.ACCESS_TOKEN_EXPIRES)
    try:
        data = serializer.loads(openid)

    except Exception as e:
        return None
    else:
        return data.get('openid')
