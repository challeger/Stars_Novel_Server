from django.urls import path, include
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    path('api/user/', include('UserApp.urls'), name='user'),
]
