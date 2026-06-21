from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Count, Q
from django.utils import timezone
from django.template.loader import render_to_string
from .models import Post, Comment, Profile, Reaction, Follow, Hashtag, Notification, Bookmark, Conversation, Message, Poll, PollOption, PollVote
from .forms import RegisterForm, PostForm, CommentForm, ProfileForm, EditPostForm, MessageForm, PollForm

POSTS_PER_PAGE = 5


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            messages.success(request, 'สมัครสมาชิกสำเร็จ! เข้าสู่ระบบได้เลย')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'feed/register.html', {'form': form})


@login_required
def feed(request):
    posts = Post.objects.select_related('author__profile').prefetch_related(
        'comments__author__profile', 'reactions'
    ).all()[:POSTS_PER_PAGE]
    user_reactions = {}
    for r in Reaction.objects.filter(user=request.user):
        user_reactions[r.post_id] = r.reaction
    bookmarked_ids = set(Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True))
    following_ids = set(Follow.objects.filter(follower=request.user).values_list('followed_id', flat=True))
    post_form = PostForm()
    comment_form = CommentForm()
    unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return render(request, 'feed/feed.html', {
        'posts': posts,
        'post_form': post_form,
        'comment_form': comment_form,
        'user_reactions': user_reactions,
        'bookmarked_ids': bookmarked_ids,
        'following_ids': following_ids,
        'unread_count': unread,
        'has_more': Post.objects.count() > POSTS_PER_PAGE,
    })


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
    return redirect('feed')


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    post.delete()
    return redirect('feed')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            if comment.author != post.author:
                Notification.objects.create(
                    recipient=post.author,
                    actor=request.user,
                    verb='comment',
                    target_post=post,
                )
    return redirect('feed')


@login_required
def toggle_reaction(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    reaction_type = request.GET.get('type', 'like')
    existing = Reaction.objects.filter(user=request.user, post=post).first()
    if existing:
        if existing.reaction == reaction_type:
            existing.delete()
            reaction_type = None
        else:
            existing.reaction = reaction_type
            existing.save()
    else:
        Reaction.objects.create(user=request.user, post=post, reaction=reaction_type)
    counts = {}
    for r in Reaction.objects.filter(post=post).values('reaction').annotate(count=Count('reaction')):
        counts[r['reaction']] = r['count']
    user_reaction = None
    if reaction_type:
        user_reaction = reaction_type
        if not existing:
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    actor=request.user,
                    verb='reaction',
                    reaction_type=reaction_type,
                    target_post=post,
                )
    return JsonResponse({
        'reaction': user_reaction,
        'counts': counts,
        'total': sum(counts.values()),
    })


def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    posts = user.posts.prefetch_related('reactions').all()
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
    follower_count = Follow.objects.filter(followed=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    user_reactions = {}
    if request.user.is_authenticated:
        for r in Reaction.objects.filter(user=request.user):
            user_reactions[r.post_id] = r.reaction
    return render(request, 'feed/profile.html', {
        'profile_user': user,
        'profile': profile,
        'posts': posts,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
        'user_reactions': user_reactions,
    })


@login_required
def toggle_follow(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({'error': 'ไม่สามารถติดตามตัวเองได้'}, status=400)
    follow, created = Follow.objects.get_or_create(follower=request.user, followed=target)
    if not created:
        follow.delete()
    else:
        Notification.objects.create(
            recipient=target,
            actor=request.user,
            verb='follow',
            target_user=request.user,
        )
    return JsonResponse({
        'following': created,
        'follower_count': Follow.objects.filter(followed=target).count(),
    })


@login_required
def edit_profile(request, username):
    if request.user.username != username:
        return redirect('feed')
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'อัปเดตโปรไฟล์สำเร็จ!')
            return redirect('profile', username=username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'feed/edit_profile.html', {'form': form})


def hashtag_posts(request, tag):
    hashtag = get_object_or_404(Hashtag, name=tag.lower())
    all_posts = hashtag.posts.select_related('author__profile').prefetch_related(
        'comments__author__profile', 'reactions'
    ).all()
    posts = all_posts[:POSTS_PER_PAGE]
    user_reactions = {}
    bookmarked_ids = set()
    if request.user.is_authenticated:
        for r in Reaction.objects.filter(user=request.user):
            user_reactions[r.post_id] = r.reaction
        bookmarked_ids = set(Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True))
    return render(request, 'feed/feed.html', {
        'posts': posts,
        'post_form': PostForm(),
        'comment_form': CommentForm(),
        'user_reactions': user_reactions,
        'bookmarked_ids': bookmarked_ids,
        'hashtag': hashtag,
        'has_more': all_posts.count() > POSTS_PER_PAGE,
    })


@login_required
def search_users(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'users': [], 'posts': []})
    users = User.objects.filter(
        Q(username__icontains=q) | Q(profile__bio__icontains=q)
    ).select_related('profile').distinct()[:5]
    posts = Post.objects.filter(text__icontains=q).select_related('author__profile')[:5]
    user_list = []
    for u in users:
        avatar_url = None
        if hasattr(u, 'profile') and u.profile and u.profile.avatar and u.profile.avatar.name:
            avatar_url = u.profile.avatar.url
        user_list.append({'username': u.username, 'avatar': avatar_url})
    return JsonResponse({
        'users': user_list,
        'posts': [{'id': p.id, 'text': p.text[:100], 'author': p.author.username} for p in posts],
    })


@login_required
def load_more_posts(request):
    offset = int(request.GET.get('offset', 0))
    tag = request.GET.get('hashtag', '')
    qs = Post.objects.select_related('author__profile').prefetch_related(
        'comments__author__profile', 'reactions'
    )
    if tag:
        qs = qs.filter(hashtags__name=tag)
    posts = qs.all()[offset:offset + POSTS_PER_PAGE]
    user_reactions = {}
    bookmarked_ids = set()
    for r in Reaction.objects.filter(user=request.user):
        user_reactions[r.post_id] = r.reaction
    bookmarked_ids = set(Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True))
    html = render_to_string('feed/_post.html', {
        'posts': posts,
        'user_reactions': user_reactions,
        'bookmarked_ids': bookmarked_ids,
        'user': request.user,
        'comment_form': CommentForm(),
    })
    return JsonResponse({
        'html': html,
        'has_more': qs.count() > offset + POSTS_PER_PAGE,
    })


@login_required
def notification_list(request):
    notifs = Notification.objects.filter(recipient=request.user).select_related('actor__profile')
    return render(request, 'feed/notifications.html', {'notifications': notifs})


@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'ok': True})


@login_required
def unread_notification_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = EditPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.is_edited = True
            post.save()
            return redirect('feed')
    else:
        form = EditPostForm(instance=post)
    return render(request, 'feed/edit_post.html', {'form': form, 'post': post})


@login_required
def toggle_bookmark(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)
    if not created:
        bookmark.delete()
    return JsonResponse({
        'bookmarked': created,
        'count': Bookmark.objects.filter(post=post).count(),
    })


@login_required
def bookmarks(request):
    post_ids = Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True)
    posts = Post.objects.filter(id__in=post_ids).select_related('author__profile').prefetch_related(
        'comments__author__profile', 'reactions'
    )
    user_reactions = {}
    for r in Reaction.objects.filter(user=request.user):
        user_reactions[r.post_id] = r.reaction
    return render(request, 'feed/bookmarks.html', {
        'posts': posts,
        'user_reactions': user_reactions,
        'comment_form': CommentForm(),
    })


@login_required
def create_repost(request, post_id):
    original = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        post = Post.objects.create(
            author=request.user,
            text=text or f"แชร์โพสต์ของ {original.author.username}",
            original_post=original,
        )
        if original.author != request.user:
            Notification.objects.create(
                recipient=original.author,
                actor=request.user,
                verb='repost',
                target_post=original,
            )
        return redirect('feed')
    return render(request, 'feed/create_repost.html', {'original': original})


def trending_hashtags(request):
    tags = Hashtag.objects.annotate(post_count=Count('posts')).filter(post_count__gt=0).order_by('-post_count')
    return render(request, 'feed/trending.html', {'tags': tags})


@login_required
def explore(request):
    posts = Post.objects.select_related('author__profile').prefetch_related(
        'comments__author__profile', 'reactions'
    ).all()[:POSTS_PER_PAGE]
    user_reactions = {}
    for r in Reaction.objects.filter(user=request.user):
        user_reactions[r.post_id] = r.reaction
    tags = Hashtag.objects.annotate(post_count=Count('posts')).filter(post_count__gt=0).order_by('-post_count')[:10]
    return render(request, 'feed/explore.html', {
        'posts': posts,
        'user_reactions': user_reactions,
        'post_form': PostForm(),
        'comment_form': CommentForm(),
        'tags': tags,
        'has_more': Post.objects.count() > POSTS_PER_PAGE,
    })


@login_required
def inbox(request):
    conversations = Conversation.objects.filter(participants=request.user).prefetch_related('participants')
    data = []
    for conv in conversations:
        other = conv.participants.exclude(id=request.user.id).first()
        last_msg = conv.messages.last()
        unread = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        data.append({
            'conversation': conv,
            'other': other,
            'last_msg': last_msg,
            'unread': unread,
        })
    return render(request, 'feed/inbox.html', {'conversations': data})


@login_required
def create_conversation(request, user_id):
    other = get_object_or_404(User, id=user_id)
    if other == request.user:
        return redirect('inbox')
    conv = Conversation.objects.filter(participants=request.user).filter(participants=other).first()
    if not conv:
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other)
    return redirect('conversation', conversation_id=conv.id)


@login_required
def conversation_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    other = conv.participants.exclude(id=request.user.id).first()
    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'feed/conversation.html', {
        'conversation': conv,
        'other': other,
        'form': MessageForm(),
    })


@login_required
def send_message(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conv
            msg.sender = request.user
            msg.save()
            other = conv.participants.exclude(id=request.user.id).first()
            if other:
                Notification.objects.create(
                    recipient=other,
                    actor=request.user,
                    verb='message',
                    target_user=request.user,
                )
    return redirect('conversation', conversation_id=conv.id)


@login_required
def vote_poll(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not hasattr(post, 'poll'):
        return JsonResponse({'error': 'ไม่มีโพล'}, status=400)
    option_id = request.POST.get('option_id')
    option = get_object_or_404(PollOption, id=option_id, poll=post.poll)
    PollVote.objects.filter(user=request.user, option__poll=post.poll).delete()
    PollVote.objects.create(user=request.user, option=option)
    return JsonResponse({'ok': True})
