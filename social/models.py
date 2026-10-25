from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import Q,F

def avatar_path(instance,filename):
    return f"avatars/{instance.user_id}/{uuid4().hex}{Path(filename).suffix.lower()}"

class Profile(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="profile")
    display_name=models.CharField(max_length=80,blank=True)
    bio=models.CharField(max_length=160,blank=True)
    avatar=models.ImageField(upload_to=avatar_path,blank=True)

class Tweet(models.Model):
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="tweets")
    body=models.TextField(validators=[MaxLengthValidator(280)])
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=["-created_at","-pk"]
        indexes=[models.Index(fields=["author","-created_at"])]

class Follow(models.Model):
    follower=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="following")
    followed=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="followers")
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["follower","followed"],name="unique_follow"),models.CheckConstraint(condition=~Q(follower=F("followed")),name="cannot_follow_self")]

class Like(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    tweet=models.ForeignKey(Tweet,on_delete=models.CASCADE,related_name="likes")
    class Meta:
        constraints=[models.UniqueConstraint(fields=["user","tweet"],name="unique_like")]

class Comment(models.Model):
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    tweet=models.ForeignKey(Tweet,on_delete=models.CASCADE,related_name="comments")
    body=models.TextField(validators=[MaxLengthValidator(280)])
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["created_at","pk"]
