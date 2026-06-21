from django.contrib import admin
from .models import Profile, Post, Comment, Reaction, Follow, Hashtag, Notification

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Reaction)
admin.site.register(Follow)
admin.site.register(Hashtag)
admin.site.register(Notification)
