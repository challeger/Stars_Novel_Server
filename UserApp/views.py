import time
import jwt
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.contrib.auth import authenticate

from UserApp.models import NovelUser, Shelf
from UserApp.permissions import IsOwnerToShelf
from Novel_Server.settings import SECRET_KEY as key
from Novel_Server.utils.user_auth import TokenAuthentication


# 登录api
class AuthView(APIView):
    def post(self, request, *args, **kwargs):
        # 用户名
        username = request.data.get('username', None)
        # 密码
        password = request.data.get('password', None)
        # 响应
        response = {
            'status': None,
            'msg': None
        }
        # 判断用户名是否存在
        if not NovelUser.object.filter(username=username):
            response['status'] = 1001
            response['msg'] = '用户名不存在!'
            return JsonResponse(response)

        # 进行登录验证
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            data = {
                'exp': int(time.time() + 60 * 60 * 24),  # 过期时间
                'iat': int(time.time()),  # 签发时间
                'username': user.username,
            }
            # 生成token
            token = jwt.encode(data, key, algorithm='HS256')
            response['status'] = 1000
            response['msg'] = '登录成功'
            # 进行编码,发送到前端
            response['token'] = token.decode('utf-8')
        elif not user:
            response['status'] = 1002
            response['msg'] = '用户名或密码错误!'
        elif not user.is_active:
            response['status'] = 1003
            response['msg'] = '用户未激活!'
        return JsonResponse(response)


# 注册api
class RegisterView(APIView):
    def post(self, request):
        response = {
            'status': None,
            'msg': None
        }
        # 用户名
        username = request.data.get('username', None)
        # 密码
        password = request.data.get('password', None)
        # 昵称
        nickname = request.data.get('nickname', None)
        # 邮箱
        email = request.data.get('email', None)
        # 性别, 默认为保密
        gender = request.data.get('gender', '保密')
        # 判断是否有重复用户名或者昵称
        if NovelUser.objects.filter(username=username):
            response['status'] = 1101
            response['msg'] = '用户名已存在!'
            return JsonResponse(response)
        elif NovelUser.objects.filter(nickname=nickname):
            response['status'] = 1102
            response['msg'] = '昵称已存在!'
        else:
            try:
                # 创建用户
                user = NovelUser.objects.create_user(username, password, email,
                                                     nickname=nickname, gender=gender)
                response['status'] = 1100
                response['msg'] = f'用户 {user.nickname} 创建成功!'
            except ValueError as e:
                response['status'] = 1103
                response['msg'] = str(e)
        return JsonResponse(response)


# 书架api get获取信息, post绑定书架
class ShelfView(APIView):
    authentication_classes = (TokenAuthentication, )

    def get(self, request):
        response = {
            'status': None,
            'msg': None,
        }
        return JsonResponse(response)

    def post(self, request):
        response = {
            'status': None,
            'msg': None,
        }
        account = request.data.get('account', None)
        password = request.data.get('password', None)
        web_url = request.data.get('web_url', None)
        shelf_title = request.data.get('shelf_title', None)
        if not account or not password or not web_url:
            response['status'] = 2001
            response['msg'] = '输入数据不合法!'
        try:
            # 创建书架
            shelf = Shelf.create(account=account, password=password, web_url=web_url,
                                 shelf_title=shelf_title, user=request.user)
            # 创建书架后获取书架信息
            response['status'] = 2000
            response['msg'] = '绑定书架成功!'
            response['shelf'] = shelf.shelf_title
        except Exception as e:
            response['status'] = 2002
            response['msg'] = str(e)
        return JsonResponse(response)

    def get_permissions(self):
        method = self.request.META.get('REQUEST_METHOD')
        permissions_classes = []
        if method == 'GET':
            permissions_classes = (IsOwnerToShelf, )
        elif method == 'POST':
            permissions_classes = (IsAuthenticated, )
        return [permission() for permission in permissions_classes]


class UserView(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        print(request.user)
        return JsonResponse({'status': 1000, 'msg': 'ok'})
