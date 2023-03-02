from django.contrib import admin
from .models import Post, PostLikes, Followers, FollowRequest

# Register your models here.

admin.site.register(Post)
admin.site.register(PostLikes)
admin.site.register(Followers)
admin.site.register(FollowRequest)
