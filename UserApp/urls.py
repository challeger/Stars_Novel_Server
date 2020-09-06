#!/user/bin/env python
# 每天都要有好心情
from django.urls import path

from UserApp import views

app_name = 'user'

urlpatterns = [
    path('user/login/', views.AuthView.as_view()),
    path('user/info/', views.UserView.as_view()),
    path('user/password/', views.PasswordView.as_view()),
    path('shelf/', views.ShelfView.as_view()),
    path('wallet/', views.WalletView.as_view()),
    path('rank/', views.RankView.as_view()),
    path('search/', views.SearchView.as_view()),
    path('book/', views.BookView.as_view()),
    path('chapter/', views.ChapterView.as_view()),
    path('lineComment/', views.LineCommentView.as_view())
]
