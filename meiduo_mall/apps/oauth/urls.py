from django.urls import path
from apps.oauth import views


urlpatterns = [
    path('qq/authorization/', views.QQLoginURLView.as_view()),
    path('oauth_callback/', views.OauthQQView.as_view()),
]
