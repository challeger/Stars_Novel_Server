#!/user/bin/env python
# 每天都要有好心情
from django.urls import path

from UserApp import views

app_name = 'user'

urlpatterns = [
    path('login/', views.AuthView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('user/', views.UserView.as_view()),
]
