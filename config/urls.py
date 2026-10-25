from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from social.views import index,UserViewSet,TweetViewSet,CommentViewSet,RegisterView,LoginView,LogoutView,MeView,PasswordView,TokenView
router=DefaultRouter()
router.register("users",UserViewSet)
router.register("tweets",TweetViewSet,basename="tweet")
router.register("comments",CommentViewSet)
urlpatterns=[path("",index),path("admin/",admin.site.urls),path("api/auth/register/",RegisterView.as_view()),path("api/auth/login/",LoginView.as_view()),path("api/auth/logout/",LogoutView.as_view()),path("api/auth/token/",TokenView.as_view()),path("api/me/",MeView.as_view()),path("api/me/password/",PasswordView.as_view()),path("api/",include(router.urls))]
