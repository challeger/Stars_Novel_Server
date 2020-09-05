#!/user/bin/env python
# 每天都要有好心情
# 用户登录验证模块
import jwt
from rest_framework import exceptions
from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication, jwt_decode_handler


class TokenAuthentication(BaseJSONWebTokenAuthentication):
    def authenticate(self, request):
        # 从请求的headers中获取认证信息
        token = request.META.get('HTTP_AUTHORIZATION', None)
        if not token:
            raise exceptions.AuthenticationFailed('用户未登录!')
        try:
            # 解密
            payload = jwt_decode_handler(token)
            # 获取用户对象
            user = self.authenticate_credentials(payload)
            # user对象会返回给request
            return user, token
        # jwt解析异常,代表非法用户,如果要当游客处理就返回None
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token已过期')
        except Exception:
            raise exceptions.AuthenticationFailed('token验证失败')
