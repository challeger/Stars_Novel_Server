from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from shortuuidfield import ShortUUIDField
from django.db import models


class UserManager(BaseUserManager):
    def _create_user(self, username, password, email, nickname, **kwargs):
        if not username:
            raise ValueError('请输入用户名!')
        if not password:
            raise ValueError('请输入密码!')
        if not email:
            raise ValueError('请输入邮箱!')
        if not nickname:
            raise ValueError('请输入昵称!')
        user = self.model(username=username, email=email, nickname=nickname, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, username, password, email, nickname, **kwargs):
        kwargs['is_superuser'] = False
        return self._create_user(username, password, email, nickname, **kwargs)

    def create_superuser(self, username, password, email, nickname, **kwargs):
        kwargs['is_superuser'] = True
        return self._create_user(username, password, email, nickname, **kwargs)


# 用户表
class NovelUser(AbstractBaseUser, PermissionsMixin):
    GENDER_TYPE = (
        ("0", "保密"),
        ("1", "男"),
        ("2", "女")
    )
    # 用户id
    uid = ShortUUIDField(primary_key=True)
    username = models.CharField(max_length=15, verbose_name='用户名', unique=True)
    nickname = models.CharField(max_length=20, verbose_name='昵称', unique=True, db_index=True)
    gender = models.CharField(max_length=2, choices=GENDER_TYPE, verbose_name='性别', default='保密', db_index=True)
    email = models.EmailField(verbose_name='邮箱')
    is_active = models.BooleanField(default=True, verbose_name='激活状态')
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nickname']
    EMAIL_FIELD = 'email'

    objects = UserManager()

    def get_full_name(self):
        return self.nickname

    def get_short_name(self):
        return self.nickname

    def __str__(self):
        return self.nickname

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        db_table = 'novel_users'


# 书架
class Shelf(models.Model):
    URL_QiDian = 'https://www.qidian.com/'
    URL_YouDu = 'https://www.youdubook.com/'
    URL_ZongHeng = 'http://www.zongheng.com/'
    URL_CiWeiMao = 'https://www.ciweimao.com/'
    URL_SET = {URL_QiDian, URL_YouDu, URL_ZongHeng, URL_CiWeiMao}
    webs = (
        (URL_QiDian, '起点中文网'),
        (URL_YouDu, '有毒小说网'),
        (URL_ZongHeng, '纵横中文网'),
        (URL_CiWeiMao, '刺猬猫'),
    )
    account = models.CharField(verbose_name='网站账号', max_length=40, unique=True)
    password = models.CharField(verbose_name='网站密码', max_length=40)
    web_url = models.URLField(verbose_name='目标网站', choices=webs, default='https://www.qidian.com/')
    shelf_title = models.CharField(verbose_name='书架标题', default='我的书架', max_length=40)
    user = models.ForeignKey('NovelUser', on_delete=models.CASCADE, related_name='user_shelf')
    books = models.ManyToManyField('Book', through='ShelfBookShip')

    def __str__(self):
        return self.shelf_title

    @classmethod
    def create(cls, account, password, web_url, shelf_title, user: NovelUser):
        # 判断输入的数据中是否有空元素
        if not all((account, password, web_url, shelf_title, user)):
            raise ValueError('输入值不能为空!')
        # 判断输入的url是否合法
        if web_url not in cls.URL_SET:
            raise ValueError('不合法的网址')
        # 判断账号是否已经使用
        if user.user_shelf.filter(account=account):
            raise ValueError('账号已在使用中!')
        # 判断书架标题是否已经存在
        if user.user_shelf.filter(shelf_title=shelf_title):
            raise ValueError('书架标题已存在!')
        # 这里需要添加账号的登录验证
        # 这里需要添加账号的登录验证
        # 返回创建的对象
        return cls.objects.create(account=account, password=password, web_url=web_url,
                                  shelf_title=shelf_title, user=user)

    class Meta:
        verbose_name = '书架'
        verbose_name_plural = verbose_name


# 书籍
class Book(models.Model):
    book_id = models.CharField(verbose_name='书籍id', max_length=50)
    book_title = models.CharField(verbose_name='书籍标题', max_length=50, null=True)
    book_cover = models.URLField(verbose_name='书籍封面',
                                 default='http://alioss.youdubook.com/uploads/picturePlaceholder.jpg')
    book_last_chapter = models.CharField(verbose_name='最新章节', max_length=100, null=True)
    book_last_chapter_url = models.URLField(verbose_name='最新章节链接', null=True)
    last_chapter = {
        'name': None,
        'url': None
    }

    def __str__(self):
        return self.book_title

    def read_history(self, shelf_id):
        return self.book_ship.filter(shelf__id=shelf_id)

    class Meta:
        verbose_name = '书籍'
        verbose_name_plural = verbose_name


# 书架&书籍 多对多表
class ShelfBookShip(models.Model):
    shelf = models.ForeignKey('Shelf', on_delete=models.CASCADE, related_name='shelf_ship')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='book_ship')
    date_joined = models.DateField(auto_now_add=True, verbose_name='收藏时间')
    last_read = models.CharField(verbose_name='最后阅读章节', max_length=100, null=True)
    last_read_url = models.URLField(verbose_name='最后阅读章节链接', null=True)
