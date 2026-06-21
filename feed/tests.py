from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Post, Comment, Reaction, Follow, Hashtag, Notification, Profile
from io import BytesIO
from PIL import Image


def create_test_image(name='test.png'):
    img = BytesIO()
    Image.new('RGB', (100, 100)).save(img, 'PNG')
    img.seek(0)
    return SimpleUploadedFile(name, img.read(), content_type='image/png')


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register(self):
        res = self.client.post(reverse('register'), {
            'username': 'newuser', 'email': 'a@b.com',
            'password1': 'Testpass123!', 'password2': 'Testpass123!',
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_required_feed(self):
        res = self.client.get(reverse('feed'))
        self.assertEqual(res.status_code, 302)


class PostTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 't@t.com', 'pass1234')
        Profile.objects.get_or_create(user=self.user)
        self.client.login(username='testuser', password='pass1234')

    def test_create_post_text_only(self):
        res = self.client.post(reverse('create_post'), {'text': 'Hello World'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)

    def test_create_post_with_image(self):
        img = create_test_image()
        res = self.client.post(reverse('create_post'), {'text': 'With img', 'image': img})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)

    def test_create_post_blank_text(self):
        res = self.client.post(reverse('create_post'), {'text': ''})
        self.assertEqual(res.status_code, 302)

    def test_delete_own_post(self):
        post = Post.objects.create(author=self.user, text='To delete')
        res = self.client.post(reverse('delete_post', args=[post.id]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Post.objects.count(), 0)

    def test_delete_other_post(self):
        other = User.objects.create_user('other', 'o@o.com', 'pass1234')
        post = Post.objects.create(author=other, text='Not mine')
        res = self.client.post(reverse('delete_post', args=[post.id]))
        self.assertEqual(res.status_code, 404)

    def test_feed_view(self):
        Post.objects.create(author=self.user, text='Post 1')
        res = self.client.get(reverse('feed'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Post 1')

    def test_hashtag_auto_parse(self):
        res = self.client.post(reverse('create_post'), {'text': 'Hello #World #test'})
        self.assertEqual(res.status_code, 302)
        post = Post.objects.first()
        self.assertEqual(post.hashtags.count(), 2)
        self.assertTrue(Hashtag.objects.filter(name='world').exists())

    def test_hashtag_page(self):
        tag = Hashtag.objects.create(name='python')
        Post.objects.create(author=self.user, text='#python post')
        res = self.client.get(reverse('hashtag_posts', args=['python']))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '#python')

    def test_load_more_no_posts(self):
        res = self.client.get(reverse('load_more_posts'), {'offset': 0})
        self.assertEqual(res.status_code, 200)
        self.assertIn('has_more', res.json())
        self.assertIn('html', res.json())

    def test_load_more_with_hashtag_filter(self):
        tag = Hashtag.objects.create(name='django')
        Post.objects.create(author=self.user, text='#django post').hashtags.add(tag)
        res = self.client.get(reverse('load_more_posts'), {'offset': 0, 'hashtag': 'django'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('django', res.json()['html'])


class ReactionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('reactor', 'r@r.com', 'pass1234')
        Profile.objects.get_or_create(user=self.user)
        self.client.login(username='reactor', password='pass1234')
        self.post = Post.objects.create(author=self.user, text='React to me')

    def test_toggle_reaction(self):
        res = self.client.get(reverse('toggle_reaction', args=[self.post.id]), {'type': 'like'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Reaction.objects.count(), 1)
        self.assertEqual(Reaction.objects.first().reaction, 'like')

    def test_toggle_reaction_removes_on_double(self):
        Reaction.objects.create(user=self.user, post=self.post, reaction='like')
        res = self.client.get(reverse('toggle_reaction', args=[self.post.id]), {'type': 'like'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_all_reaction_types(self):
        for rev in ['like', 'love', 'laugh', 'wow', 'sad', 'angry']:
            res = self.client.get(reverse('toggle_reaction', args=[self.post.id]), {'type': rev})
            self.assertEqual(res.status_code, 200)
        self.assertEqual(Reaction.objects.count(), 1)


class CommentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('commenter', 'c@c.com', 'pass1234')
        Profile.objects.get_or_create(user=self.user)
        self.client.login(username='commenter', password='pass1234')
        self.post = Post.objects.create(author=self.user, text='Comment here')

    def test_add_comment(self):
        res = self.client.post(reverse('add_comment', args=[self.post.id]), {'text': 'Nice post!'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().text, 'Nice post!')

    def test_add_comment_blank(self):
        res = self.client.post(reverse('add_comment', args=[self.post.id]), {'text': ''})
        self.assertEqual(res.status_code, 302)

    def test_comment_notification(self):
        other = User.objects.create_user('author', 'a@a.com', 'pass1234')
        post = Post.objects.create(author=other, text='My post')
        self.client.post(reverse('add_comment', args=[post.id]), {'text': 'Comment!'})
        self.assertTrue(Notification.objects.filter(recipient=other, verb='comment').exists())


class FollowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('follower', 'f@f.com', 'pass1234')
        Profile.objects.get_or_create(user=self.user)
        self.client.login(username='follower', password='pass1234')
        self.target = User.objects.create_user('target', 't@t.com', 'pass1234')
        Profile.objects.get_or_create(user=self.target)

    def test_follow_user(self):
        res = self.client.post(reverse('toggle_follow', args=['target']))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Follow.objects.filter(follower=self.user, followed=self.target).exists())

    def test_unfollow_user(self):
        Follow.objects.create(follower=self.user, followed=self.target)
        res = self.client.post(reverse('toggle_follow', args=['target']))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_notification(self):
        self.client.post(reverse('toggle_follow', args=['target']))
        self.assertTrue(Notification.objects.filter(recipient=self.target, verb='follow').exists())

    def test_cannot_follow_self(self):
        res = self.client.post(reverse('toggle_follow', args=['follower']))
        self.assertEqual(res.status_code, 400)

    def test_profile_view_counts(self):
        Follow.objects.create(follower=self.user, followed=self.target)
        res = self.client.get(reverse('profile', args=['target']))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '1')


class SearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('searchuser', 's@s.com', 'pass1234')
        Profile.objects.get_or_create(user=self.user)
        self.client.login(username='searchuser', password='pass1234')

    def test_search_users(self):
        User.objects.create_user('founduser', 'u@u.com', 'pass1234')
        res = self.client.get(reverse('search'), {'q': 'found'})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        usernames = [u['username'] for u in data.get('users', [])]
        self.assertIn('founduser', usernames)

    def test_search_no_query(self):
        res = self.client.get(reverse('search'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get('users', []), [])
        self.assertEqual(data.get('posts', []), [])


class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('profuser', 'p@p.com', 'pass1234')
        self.profile, _ = Profile.objects.get_or_create(user=self.user)
        self.client.login(username='profuser', password='pass1234')

    def test_edit_profile_bio(self):
        res = self.client.post(reverse('edit_profile', args=['profuser']), {'bio': 'Hello!'})
        self.assertEqual(res.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Hello!')

    def test_edit_profile_image(self):
        img = create_test_image()
        res = self.client.post(reverse('edit_profile', args=['profuser']), {'avatar': img, 'bio': 'new bio'})
        self.assertEqual(res.status_code, 302)

    def test_edit_profile_image_too_large(self):
        large = SimpleUploadedFile('large.png', b'x' * (6 * 1024 * 1024), content_type='image/png')
        res = self.client.post(reverse('edit_profile', args=['profuser']), {'avatar': large, 'bio': 'bio'})
        self.assertEqual(res.status_code, 200)

    def test_edit_profile_wrong_format(self):
        bad = SimpleUploadedFile('bad.gif', b'GIF89a', content_type='image/gif')
        res = self.client.post(reverse('edit_profile', args=['profuser']), {'avatar': bad, 'bio': 'bio'})
        self.assertEqual(res.status_code, 200)


class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('notifuser', 'n@n.com', 'pass1234')
        Profile.objects.get_or_create(user=self.user)
        self.client.login(username='notifuser', password='pass1234')

    def test_notification_list(self):
        res = self.client.get(reverse('notifications'))
        self.assertEqual(res.status_code, 200)

    def test_mark_notification_read(self):
        n = Notification.objects.create(recipient=self.user, actor=self.user, verb='follow')
        res = self.client.get(reverse('mark_notification_read', args=[n.id]))
        self.assertEqual(res.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_unread_count(self):
        Notification.objects.create(recipient=self.user, actor=self.user, verb='follow')
        res = self.client.get(reverse('unread_notification_count'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['count'], 1)
