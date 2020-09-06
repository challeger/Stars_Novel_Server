#!/user/bin/env python
# 每天都要有好心情
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from UserApp.models import NovelUser, Shelf, Book, ShelfBookShip


class NovelUserSerializer(ModelSerializer):
    class Meta:
        model = NovelUser
        fields = ('nickname', 'username', 'gender', 'email', )


class ShelfBookShipSerializer(ModelSerializer):
    class Meta:
        model = ShelfBookShip
        fields = ('date_joined', 'last_read', 'last_read_url')


class BookSerializer(ModelSerializer):
    # 是否收藏了本书
    is_favo = SerializerMethodField('get_is_favo', label='已收藏')
    # 是否有观看历史
    read_history = SerializerMethodField('get_read_history', label='上次看到')

    class Meta:
        model = Book
        fields = ('id', 'book_id', 'book_title', 'book_cover',
                  'last_chapter', 'is_favo', 'read_history')

    def get_is_favo(self, obj):
        # 从传入的上下文中获取当前的书架,并判断两者是否有多对多关系,有则表示已关注.
        shelf = obj.shelf_set.filter(id=self.context.get('shelf_id', None))
        return shelf is not None

    def get_read_history(self, obj):
        history = obj.read_history(self.context.get('shelf_id', None))
        if history:
            # 进行数据序列化
            data = ShelfBookShipSerializer(history[0], context={'request': self.context['request']}).data
            return data
        return None


class ShelfSerializer(ModelSerializer):
    user = NovelUserSerializer(read_only=True)
    book_set = SerializerMethodField('get_book_set', label='收藏书籍')

    class Meta:
        model = Shelf
        fields = ('user', 'id', 'shelf_title', 'web_url', 'book_set',
                  'account')

    def get_book_set(self, obj):
        book_set = obj.books.all()
        data = BookSerializer(book_set, many=True, context={'request': self.context['request'],
                                                            'shelf': obj.id}).data
        return data
