from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Profile,Tweet,Comment

class UserSerializer(serializers.ModelSerializer):
    display_name=serializers.SerializerMethodField()
    bio=serializers.SerializerMethodField()
    avatar=serializers.SerializerMethodField()
    followers_count=serializers.SerializerMethodField()
    following_count=serializers.SerializerMethodField()
    is_followed=serializers.SerializerMethodField()
    class Meta:
        model=get_user_model()
        fields=["id","username","display_name","bio","avatar","followers_count","following_count","is_followed"]
    def get_display_name(self,obj):
        return getattr(getattr(obj,"profile",None),"display_name","") or obj.username
    def get_bio(self,obj):
        return getattr(getattr(obj,"profile",None),"bio","")
    def get_avatar(self,obj):
        profile=getattr(obj,"profile",None)
        return f"/api/users/{obj.pk}/avatar/" if profile and profile.avatar else None
    def get_followers_count(self,obj):return obj.followers.count()
    def get_following_count(self,obj):return obj.following.count()
    def get_is_followed(self,obj):
        user=self.context.get("request").user
        return user.is_authenticated and obj.followers.filter(follower=user).exists()

class RegistrationSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)
    class Meta:
        model=get_user_model()
        fields=["username","password"]
    def validate(self,attrs):
        user=get_user_model()(username=attrs["username"])
        try:validate_password(attrs["password"],user)
        except DjangoValidationError as exc:raise serializers.ValidationError({"password":exc.messages})
        return attrs
    def create(self,attrs):
        user=get_user_model().objects.create_user(**attrs)
        Profile.objects.create(user=user)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=Profile
        fields=["display_name","bio","avatar"]
    def validate_avatar(self,value):
        if value and value.size>3*1024*1024:
            raise serializers.ValidationError("Escolha uma imagem de até 3 MB.")
        return value

class TweetSerializer(serializers.ModelSerializer):
    author=UserSerializer(read_only=True)
    likes_count=serializers.SerializerMethodField()
    comments_count=serializers.SerializerMethodField()
    liked=serializers.SerializerMethodField()
    body=serializers.CharField(max_length=280,trim_whitespace=True,allow_blank=False)
    class Meta:
        model=Tweet
        fields=["id","author","body","created_at","updated_at","likes_count","comments_count","liked"]
    def get_likes_count(self,obj):return obj.likes.count()
    def get_comments_count(self,obj):return obj.comments.count()
    def get_liked(self,obj):
        user=self.context["request"].user
        return user.is_authenticated and obj.likes.filter(user=user).exists()

class CommentSerializer(serializers.ModelSerializer):
    author=UserSerializer(read_only=True)
    body=serializers.CharField(max_length=280,trim_whitespace=True,allow_blank=False)
    class Meta:
        model=Comment
        fields=["id","author","body","created_at"]
