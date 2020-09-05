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
