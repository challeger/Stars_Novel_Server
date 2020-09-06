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
from Novel_Server.utils.spiders import Spider_YouDu, SPIDERS


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


# 获取书架,如果有id就返回单个书架,否则返回用户的所有书架
def get_shelf(request, shelf_id):
    return request.user.user_shelf.all() if not shelf_id else request.user.user_shelf.filter(id=shelf_id)


# 书架api get获取信息, put绑定书架, post修改书架信息
class ShelfView(GenericAPIView):
    authentication_classes = (TokenAuthentication, )

    def get(self, request: Request):
        response = {
            'status': 2000,
            'msg': None,
        }
        shelf_id = request.data.get('shelf_id')
        shelf_set = get_shelf(request, shelf_id)
        if shelf_set:
            try:
                data = ShelfSerializer(shelf_set, many=True, context={'request': request}).data
                response['msg'] = '获取书架信息成功'
                response['data'] = data
            except ValueError as e:
                response['status'] = 2002
                response['msg'] = str(e)
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


class WalletView(APIView):
    """
    钱包接口
    get: 获取书架中的代币余额.
    """
    authentication_classes = (TokenAuthentication, )
    permissions_classes = (IsOwnerToShelf, )

    def get(self, request):
        response = {
            'status': None,
            'msg': None
        }
        data = dict()
        shelf_id = request.data.get('shelf_id', None)
        if not shelf_id:
            shelf_set = request.user.user_shelf.all()
        else:
            shelf_set = request.user.user_shelf.filter(id=shelf_id)
        try:
            for shelf in shelf_set:
                if shelf.spider:
                    data[shelf.id] = {
                        'shelf_id': shelf.id,
                        'shelf_title': shelf.shelf_title,
                        'wallet': shelf.spider.get_wallet()
                    }
            response['status'] = 2000
            response['msg'] = '获取钱包信息成功!'
            response['data'] = data
        except ValueError as e:
            response['status'] = 2002
            response['msg'] = str(e)
        return Response(response)


class RankView(APIView):
    """
    排行榜数据接口
    get: 获取排行榜信息, 当不传入shelf_id时,默认获取所有书架的排行榜
    """
    authentication_classes = (TokenAuthentication, )

    def get(self, request):
        response = {
            'status': None,
            'msg': None
        }
        rank_type = request.query_params.get('rank_type')
        data_type = request.query_params.get('data_type')
        page = request.query_params.get('page')
        data = {}
        shelf_id = request.data.get('shelf_id', None)
        shelf_set = get_shelf(request, shelf_id)
        try:
            for shelf in shelf_set:
                if shelf.spider:
                    data[shelf.id] = {
                        'shelf_id': shelf.id,
                        'shelf_title': shelf.shelf_title,
                        'rank': shelf.spider.get_rank(rank_type, data_type, page)
                    }
            response['status'] = 2000
            response['msg'] = '获取排行榜信息成功!'
            response['data'] = data
        except ValueError as e:
            response['status'] = 2002
            response['msg'] = str(e)
        return Response(response)


class SearchView(APIView):
    authentication_classes = (TokenAuthentication, )

    def get(self, request):
        response = {
            'status': None,
            'msg': None
        }
        keyword = request.query_params.get('keyword', None)
        page = request.query_params.get('page', 1)
        # 有就单独搜索,没有的话就在所有书架搜索
        shelf_id = request.data.get('shelf_id', None)
        data = {}
        if keyword:
            shelf_set = get_shelf(request, shelf_id)
            try:
                for shelf in shelf_set:
                    if shelf.spider:
                        data[shelf.id] = {
                            'shelf_id': shelf.id,
                            'shelf_title': shelf.shelf_title,
                            'rank': shelf.spider.search_book(keyword, page)
                        }
                response['data'] = data
            except ValueError as e:
                response['status'] = 2002
                response['msg'] = str(e)
        else:
            response['status'] = 3001
            response['msg'] = '请输入关键词!'
        return Response(response)


class BookView(APIView):
    """
    书籍接口
    get: 获取书籍详情信息,需要 shelf_id, book_id
    post: 收藏&取消收藏书籍, 需要shelf_id, book_id
    """
    authentication_classes = (TokenAuthentication, )

    def get(self, request):
        response = {
            'status': 4001,
            'msg': '未找到书籍!'
        }
        book_id = request.data.get('book_id', None)
        shelf_id = request.data.get('shelf_id', None)

        if book_id and shelf_id:
            # 只能获取一个书架的一本书
            shelf = get_shelf(request, shelf_id)[0]
            try:
                if shelf.spider:
                    response['status'] = 4000
                    response['msg'] = '获取书籍信息成功'
                    response['data'] = shelf.spider.get_book(book_id)
            except ValueError as e:
                response['status'] = 2001
                response['msg'] = str(e)

        return Response(response)

    def post(self, request):
        response = {
            'status': 4001,
            'msg': '未找到书籍!'
        }
        book_id = request.data.get('book_id', None)
        shelf_id = request.data.get('shelf_id', None)
        if book_id and shelf_id:
            # 只能获取一个书架的一本书
            shelf = get_shelf(request, shelf_id)[0]
            try:
                if shelf.spider:
                    response = shelf.spider.favo_book(book_id)
            except ValueError as e:
                response['status'] = 2001
                response['msg'] = str(e)

        return Response(response)


class ChapterView(APIView):
    """
    章节接口
    get: 获取章节信息 需要shelf_id, book_id, chapter_id
    post: 订阅章节 需要shelf_id, book_id, chapter_id
    """
    authentication_classes = (TokenAuthentication, )

    def get(self, request):
        # 获取章节信息
        response = {
            'status': 2001,
            'msg': None
        }
        shelf_id = request.data.get('shelf_id')
        book_id = request.data.get('book_id')
        chapter_id = request.data.get('chapter_id')
        if shelf_id and book_id and chapter_id:
            # 必须传入shelf_id
            shelf = get_shelf(request, shelf_id)[0]
            try:
                if shelf and shelf.spider:
                    data = shelf.spider.get_chapter(chapter_id)
                    response['status'] = 2000
                    response['msg'] = '获取章节信息成功'
                    response['data'] = data
            except ValueError as e:
                response['msg'] = str(e)
        return Response(response)

    def post(self, request):
        # 订阅章节
        response = {
            'status': 2001,
            'msg': None
        }
        shelf_id = request.data.get('shelf_id')
        book_id = request.data.get('book_id')
        chapter_id = request.data.get('chapter_id')
        if shelf_id and book_id and chapter_id:
            # 必须传入shelf_id
            shelf = get_shelf(request, shelf_id)[0]
            try:
                if shelf and shelf.spider:
                    data = shelf.spider.buy_chapter(book_id, chapter_id)
                    response = data
            except ValueError as e:
                response['msg'] = str(e)
        return Response(response)


class LineCommentView(APIView):
    """
    间贴接口
    get: 获取间贴, 需要shelf_id, chapter_id, count, index
    post: 发送间贴, 需要shelf_id, chapter_id, book_id, index, line_content, tsukkomi_content
    """
    authentication_classes = (TokenAuthentication, )

    def get(self, request):
        """
        获取间贴信息
        :param request:
        :return:
        """
        response = {
            'status': 2001,
            'msg': None
        }
        shelf_id = request.data.get('shelf_id')
        chapter_id = request.data.get('chapter_id')
        count = request.data.get('count', 10)
        index = request.data.get('index')
        if shelf_id and chapter_id and index:
            # 必须传入shelf_id
            shelf = get_shelf(request, shelf_id)[0]
            try:
                if shelf and shelf.spider:
                    data = shelf.spider.get_line_comment(chapter_id, count, index)
                    response['status'] = 1
                    response['msg'] = '获取间贴信息成功'
                    response['data'] = data
            except ValueError as e:
                response['msg'] = str(e)
        return Response(response)

    def post(self, request):
        """
        发送间贴信息
        :param request:
        :return:
        """
        response = {
            'status': 2001,
            'msg': '数据错误'
        }
        shelf_id = request.data.get('shelf_id')
        book_id = request.data.get('book_id')
        chapter_id = request.data.get('chapter_id')
        index = request.data.get('index')
        line_content = request.data.get('line_content')
        tsukkomi_content = request.data.get('tsukkomi_content')
        # 都不为空
        if all((shelf_id, book_id, chapter_id, index, line_content, tsukkomi_content)):
            shelf = get_shelf(request, shelf_id)[0]
            try:
                if shelf and shelf.spider:
                    data = shelf.spider.send_line_comment(book_id, chapter_id, index,
                                                          line_content, tsukkomi_content)
                    response = data
            except ValueError as e:
                response['msg'] = str(e)
        return Response(response)
