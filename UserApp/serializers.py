#!/user/bin/env python
# 每天都要有好心情
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from UserApp.models import NovelUser, Shelf


class NovelUserSerializer(ModelSerializer):
    class Meta:
        model = NovelUser
        fields = ('nickname', 'username', 'gender', 'email', )


class ShelfSerializer(ModelSerializer):
    user = NovelUserSerializer(read_only=True)
    books = SerializerMethodField('get_books')

    class Meta:
        model = Shelf
        fields = ('user', 'id', 'shelf_title', 'web_url', 'books',
                  'account')

    def get_books(self, obj: Shelf):
        data = None
        try:
            if obj.spider:
                data = obj.spider.get_shelf()
        except ValueError as e:
            raise e
        return data
