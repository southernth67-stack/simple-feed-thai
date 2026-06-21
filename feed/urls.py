from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.feed, name='feed'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='feed/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/react/', views.toggle_reaction, name='toggle_reaction'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('hashtag/<str:tag>/', views.hashtag_posts, name='hashtag_posts'),
    path('search/', views.search_users, name='search'),
    path('load-more/', views.load_more_posts, name='load_more_posts'),
    path('notifications/', views.notification_list, name='notifications'),
    path('notifications/read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/unread-count/', views.unread_notification_count, name='unread_notification_count'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('post/<int:post_id>/repost/', views.create_repost, name='create_repost'),
    path('trending/', views.trending_hashtags, name='trending'),
    path('explore/', views.explore, name='explore'),
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:user_id>/', views.create_conversation, name='create_conversation'),
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('post/<int:post_id>/poll/vote/', views.vote_poll, name='vote_poll'),
]
