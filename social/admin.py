from django.contrib import admin
from .models import Profile,Tweet,Follow,Like,Comment
for model in [Profile,Tweet,Follow,Like,Comment]:admin.site.register(model)
