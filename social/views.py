from django.contrib.auth import authenticate,login,logout,get_user_model,update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse,Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie,csrf_protect
from rest_framework import status,viewsets,permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError,PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import ScopedRateThrottle
from .models import Profile,Tweet,Follow,Like,Comment
from .serializers import UserSerializer,RegistrationSerializer,ProfileSerializer,TweetSerializer,CommentSerializer

@ensure_csrf_cookie
def index(request):return render(request,"social/index.html")

class TokenView(ObtainAuthToken):
    throttle_classes=[ScopedRateThrottle]
    throttle_scope="auth"

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self,request,view,obj):
        return request.method in permissions.SAFE_METHODS or obj.author_id==request.user.pk

@method_decorator(csrf_protect,name="dispatch")
class RegisterView(APIView):
    permission_classes=[permissions.AllowAny]
    throttle_scope="auth"
    def post(self,request):
        serializer=RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.save()
        login(request,user)
        return Response(UserSerializer(user,context={"request":request}).data,status=201)

@method_decorator(csrf_protect,name="dispatch")
class LoginView(APIView):
    permission_classes=[permissions.AllowAny]
    throttle_scope="auth"
    def post(self,request):
        user=authenticate(request,username=request.data.get("username"),password=request.data.get("password"))
        if user is None:raise ValidationError({"detail":"Usuário ou senha inválidos."})
        login(request,user)
        return Response(UserSerializer(user,context={"request":request}).data)

class LogoutView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request):
        logout(request)
        return Response(status=204)

class MeView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request):return Response(UserSerializer(request.user,context={"request":request}).data)
    def patch(self,request):
        profile,_=Profile.objects.get_or_create(user=request.user)
        serializer=ProfileSerializer(profile,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True);serializer.save()
        request.user._state.fields_cache.pop("profile",None)
        return self.get(request)

class PasswordView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request):
        if not request.user.check_password(request.data.get("old_password","")):
            raise ValidationError({"old_password":"Senha atual inválida."})
        password=request.data.get("new_password","")
        try:validate_password(password,request.user)
        except DjangoValidationError as exc:raise ValidationError({"new_password":exc.messages})
        request.user.set_password(password);request.user.save()
        request.user.auth_token.delete() if hasattr(request.user,"auth_token") else None
        update_session_auth_hash(request,request.user)
        return Response({"detail":"Senha atualizada."})

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=get_user_model().objects.select_related("profile").order_by("username")
    serializer_class=UserSerializer
    search_fields=["username"]
    def get_queryset(self):
        queryset=super().get_queryset()
        query=self.request.query_params.get("search","")
        return queryset.filter(username__icontains=query) if query else queryset
    @action(detail=True,methods=["post","delete"],permission_classes=[permissions.IsAuthenticated])
    def follow(self,request,pk=None):
        user=self.get_object()
        if user==request.user:raise ValidationError({"detail":"Você não pode seguir a si mesmo."})
        if request.method=="POST":
            Follow.objects.get_or_create(follower=request.user,followed=user)
        else:Follow.objects.filter(follower=request.user,followed=user).delete()
        return Response(self.get_serializer(user).data)
    def relation(self,users):
        page=self.paginate_queryset(users)
        serializer=self.get_serializer(page if page is not None else users,many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
    @action(detail=True,methods=["get"])
    def followers(self,request,pk=None):
        return self.relation(get_user_model().objects.filter(following__followed=self.get_object()).select_related("profile").order_by("username"))
    @action(detail=True,methods=["get"])
    def following(self,request,pk=None):
        return self.relation(get_user_model().objects.filter(followers__follower=self.get_object()).select_related("profile").order_by("username"))
    @action(detail=True,methods=["get"],permission_classes=[permissions.AllowAny])
    def avatar(self,request,pk=None):
        profile=getattr(self.get_object(),"profile",None)
        if not profile or not profile.avatar:raise Http404
        try:return FileResponse(profile.avatar.open("rb"))
        except FileNotFoundError:raise Http404

class TweetViewSet(viewsets.ModelViewSet):
    serializer_class=TweetSerializer
    permission_classes=[permissions.IsAuthenticatedOrReadOnly,IsAuthorOrReadOnly]
    def get_queryset(self):
        queryset=Tweet.objects.select_related("author__profile").prefetch_related("likes","comments")
        author=self.request.query_params.get("author")
        return queryset.filter(author_id=author) if author and author.isdigit() else queryset
    def perform_create(self,serializer):serializer.save(author=self.request.user)
    @action(detail=False,methods=["get"],permission_classes=[permissions.IsAuthenticated])
    def feed(self,request):
        queryset=self.get_queryset().filter(author_id__in=Follow.objects.filter(follower=request.user).values("followed_id"))
        page=self.paginate_queryset(queryset)
        return self.get_paginated_response(self.get_serializer(page,many=True).data)
    @action(detail=True,methods=["post","delete"],permission_classes=[permissions.IsAuthenticated])
    def like(self,request,pk=None):
        tweet=self.get_object()
        if request.method=="POST":Like.objects.get_or_create(user=request.user,tweet=tweet)
        else:Like.objects.filter(user=request.user,tweet=tweet).delete()
        tweet._prefetched_objects_cache = {}
        return Response(self.get_serializer(tweet).data)
    @action(detail=True,methods=["get","post"],permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def comments(self,request,pk=None):
        tweet=self.get_object()
        if request.method=="POST":
            serializer=CommentSerializer(data=request.data,context={"request":request})
            serializer.is_valid(raise_exception=True);serializer.save(author=request.user,tweet=tweet)
            return Response(serializer.data,status=201)
        comments=tweet.comments.select_related("author__profile").all()
        page=self.paginate_queryset(comments)
        return self.get_paginated_response(CommentSerializer(page,many=True,context={"request":request}).data)

class CommentViewSet(viewsets.GenericViewSet):
    queryset=Comment.objects.all()
    permission_classes=[permissions.IsAuthenticated,IsAuthorOrReadOnly]
    def destroy(self,request,pk=None):
        comment=self.get_object();comment.delete()
        return Response(status=204)

