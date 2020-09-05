# 自定义的权限验证
from rest_framework import permissions

from UserApp.models import NovelUser, Shelf


class IsOwnerToShelf(permissions.BasePermission):
    message = '没找到对应书架呢'

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            shelf_id = request.query_params.get('shelf_id', None)
            if request.user.user_shelf.filter(id=shelf_id):
                return True
        return False
