from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall.settings import SECRET_KEY


def generic_email_verify_token(user_id):
    s = Serializer(secret_key=SECRET_KEY, expires_in=3600*24)
    data = s.dumps({'user_id': user_id})
    return data.decode()


def check_email_verify_token(token):
    s = Serializer(secret_key=SECRET_KEY, expires_in=3600*24)
    try:
        result = s.loads(token)
    except Exception:
        return None
    return result.get('user_id')


