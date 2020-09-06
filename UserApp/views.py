import time
import jwt
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate

from UserApp.models import NovelUser, Shelf
from UserApp.permissions import IsOwnerToShelf
from UserApp.serializers import ShelfSerializer, NovelUserSerializer
from Novel_Server.settings import SECRET_KEY as key
from Novel_Server.utils.user_auth import TokenAuthentication


# 登录api
class AuthView(APIView):
    def post(self, request: Request):
        """
        用户登录
        :param request: 请求
        :return:
        """
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
        if not NovelUser.objects.filter(username=username):
            response['status'] = 1001
            response['msg'] = '用户名不存在!'
            return Response(response)

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
        return Response(response)


# 书架api get获取信息, post绑定书架, put创建书架
class ShelfView(GenericAPIView):
    authentication_classes = (TokenAuthentication, )

    def get_queryset(self):
        user = self.request.user
        return user.user_shelf.all()

    def get(self, request: Request):
        response = {
            'status': 2000,
            'msg': None,
        }
        shelf_set = self.get_queryset()
        if shelf_set:
            data = ShelfSerializer(shelf_set, many=True, context={'request': request}).data
            response['msg'] = '获取书架信息成功'
            response['data'] = data
        else:
            response['status'] = 2001
            response['msg'] = '还没有绑定书架!快去绑定一个吧!'
        return Response(response)

    def put(self, request: Request):
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
        return Response(response)

    def post(self, request: Request):
        """
        修改书架信息
        :param request: 包含数据:shelf_id,account,password,shelf_title
        :return:
        """
        response = {
            'status': None,
            'msg': None
        }
        shelf_id = request.data.get('shelf_id')
        try:
            shelf = Shelf.objects.get(id=shelf_id)
            shelf.account = request.data.get('account', shelf.account)
            shelf.password = request.data.get('password', shelf.password)
            shelf.shelf_title = request.data.get('shelf_title', shelf.shelf_title)
            # 如果修改了账号密码,应该对是否能登录对应网站进行验证..
            shelf.save()
            response['status'] = 2000
            response['msg'] = '修改书架信息成功!'
        except Shelf.DoesNotExist:
            response['status'] = '2001'
            response['msg'] = '未找到书架!'
        return Response(response)

    def get_permissions(self):
        method = self.request.META.get('REQUEST_METHOD')
        permissions_classes = []
        if method == 'GET':
            permissions_classes = (IsAuthenticated, )
        elif method == 'PUT':
            permissions_classes = (IsAuthenticated, )
        elif method == 'POST':
            permissions_classes = (IsOwnerToShelf, )
        return [permission() for permission in permissions_classes]


class UserView(APIView):

    def get(self, request):
        response = {
            'status': 1000,
            'msg': '获取用户信息成功',
            'data': None
        }
        uid = request.data.get('uid', None)
        try:
            user = NovelUser.objects.get(uid=uid)
            data = NovelUserSerializer(user, context={'request': request}).data
            response['data'] = data
        except NovelUser.DoesNotExist:
            response['status'] = 1001
            response['msg'] = '用户不存在!'
        return Response(response)

    def put(self, request: Request):
        """
        创建用户
        :param request: 请求
        :return:
        """
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
            return Response(response)
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
        return Response(response)

    def post(self, request: Request):
        """
        修改用户信息.
        :param request:
        :return:
        """
        response = {
            'status': None,
            'msg': None
        }
        user = request.user
        try:
            user.update_info(request.data)
            response['status'] = 1000
            response['msg'] = '修改用户信息成功!'
        except ValueError as e:
            response['status'] = 1101
            response['msg'] = str(e)
        return Response(response)

    def get_permissions(self):
        method = self.request.META.get('REQUEST_METHOD')
        if method == 'POST':
            # 修改用户信息必须登录
            permissions_classes = (IsAuthenticated, )
            self.authentication_classes = (TokenAuthentication, )
        else:
            # 创建用户无需权限
            permissions_classes = (AllowAny, )
        return [permission() for permission in permissions_classes]


class PasswordView(APIView):
    authentication_classes = (TokenAuthentication, )
    permissions_classes = (IsAuthenticated, )

    def post(self, request: Request):
        response = {
            'status': None,
            'msg': None
        }
        old_password = request.data.get('old_password', None)
        new_password = request.data.get('new_password', None)
        if request.user.check_password(old_password):
            request.user.set_password(new_password)
            response['status'] = 1000
            response['msg'] = '修改密码成功'
        else:
            response['status'] = 1002
            response['msg'] = '原密码错误!'
        return Response(response)
