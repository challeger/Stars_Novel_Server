from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from shortuuidfield import ShortUUIDField
from django.db import models

from Novel_Server.utils.spiders import Spider_YouDu
from Novel_Server.utils.spiders_setting import SPIDERS


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
    GENDER_SET = {'男', '女', '保密'}
    GENDER_TYPE = (
        ("保密", "保密"),
        ("男", "男"),
        ("女", "女")
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

    def update_info(self, data):
        gender = data.get('gender', self.gender)
        self.email = data.get('email', self.email)
        nickname = data.get('nickname', self.nickname)
        if nickname != self.nickname and NovelUser.objects.filter(nickname=nickname):
            raise ValueError('该昵称已存在!')
        if gender not in self.GENDER_SET:
            raise ValueError('不合法的数据')
        self.nickname = nickname
        self.gender = gender
        self.save()

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
    account = models.CharField(verbose_name='网站账号', max_length=40)
    password = models.CharField(verbose_name='网站密码', max_length=40)
    web_url = models.URLField(verbose_name='目标网站', choices=webs, default='https://www.qidian.com/')
    shelf_title = models.CharField(verbose_name='书架标题', default='我的书架', max_length=40)
    user = models.ForeignKey('NovelUser', on_delete=models.CASCADE, related_name='user_shelf')

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
        if user.user_shelf.filter(account=account, web_url=web_url):
            raise ValueError('账号已在使用中!')
        # 判断书架标题是否已经存在
        if user.user_shelf.filter(shelf_title=shelf_title):
            raise ValueError('书架标题已存在!')
        # 这里需要添加账号的登录验证
        # 这里需要添加账号的登录验证
        # 返回创建的对象
        return cls.objects.create(account=account, password=password, web_url=web_url,
                                  shelf_title=shelf_title, user=user)

    @property
    def books(self):
        try:
            spider = globals()[SPIDERS[self.web_url]](self)
            # 判断是否登录
            if not spider.is_login:
                spider.login()
            data = spider.get_shelf()
        except KeyError:
            data = None
        return data

    class Meta:
        verbose_name = '书架'
        verbose_name_plural = verbose_name
