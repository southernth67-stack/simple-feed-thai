import re
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.user.username


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['follower', 'followed']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower} follows {self.followed}"


class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"#{self.name}"


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    text = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    hashtags = models.ManyToManyField(Hashtag, related_name='posts', blank=True)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    original_post = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='reposts')

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self._parse_hashtags()
            self._parse_mentions()

    def _parse_hashtags(self):
        names = re.findall(r'#(\w+)', self.text)
        for name in names:
            tag, _ = Hashtag.objects.get_or_create(name=name.lower())
            self.hashtags.add(tag)

    def _parse_mentions(self):
        usernames = re.findall(r'@(\w+)', self.text)
        for name in usernames:
            try:
                mentioned = User.objects.get(username=name)
                if mentioned != self.author:
                    Notification.objects.get_or_create(
                        recipient=mentioned,
                        actor=self.author,
                        verb='mention',
                        target_post=self,
                    )
            except User.DoesNotExist:
                pass

    def is_repost(self):
        return self.original_post is not None

    def __str__(self):
        return f"{self.author.username}: {self.text[:50]}"


REACTION_CHOICES = [
    ('like', '👍'),
    ('love', '😍'),
    ('laugh', '😂'),
    ('wow', '😮'),
    ('sad', '😢'),
    ('angry', '😡'),
]


class Reaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'post']

    def __str__(self):
        return f"{self.user.username} {self.reaction} post {self.post.id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username}: {self.text[:50]}"


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'post']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.post.id}"


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Conversation {self.id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.text[:50]}"


class Poll(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll')
    question = models.CharField(max_length=300)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text


class PollVote(models.Model):
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['option', 'user']

    def __str__(self):
        return f"{self.user.username} -> {self.option.text}"


class Notification(models.Model):
    VERB_CHOICES = [
        ('reaction', 'reaction'),
        ('comment', 'comment'),
        ('follow', 'follow'),
        ('mention', 'mention'),
        ('repost', 'repost'),
        ('message', 'message'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor_notifications')
    verb = models.CharField(max_length=10, choices=VERB_CHOICES)
    reaction_type = models.CharField(max_length=10, blank=True, null=True)
    target_post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='target_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor} {self.verb} -> {self.recipient}"
