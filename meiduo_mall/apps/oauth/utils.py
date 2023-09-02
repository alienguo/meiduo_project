from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall.settings import SECRET_KEY


def generic_openid(openid):
    s = Serializer(secret_key=SECRET_KEY, expires_in=3600)
    access_token = s.dumps({'openid': openid})

    # bytes数据转换为str
    return access_token.decode()


# 对数据解密
def check_access_token(token):
    s = Serializer(secret_key=SECRET_KEY, expires_in=3600)
    try:
        result = s.loads(token)
    except Exception:
        return None
    else:
        return result.get('openid')
