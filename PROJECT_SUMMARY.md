# Simple Feed - Project Summary

## Stack
- Python 3.10 + Django 5.2
- SQLite (db.sqlite3)
- Bootstrap 5.3 + Bootstrap Icons
- Google Font: Prompt (Thai)
- Pillow (image upload)

## How to Run
```bash
cd simple_feed
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# Open http://localhost:8000
```

## Models (feed/models.py)
| Model | Fields |
|-------|--------|
| Profile | user, avatar, cover_image, bio |
| Post | author, text, image, hashtags (M2M), created_at |
| Comment | post (FK), author, text, created_at |
| Reaction | user, post, reaction (like/love/laugh/wow/sad/angry) |
| Follow | follower, followed, created_at |
| Hashtag | name (unique) |
| Notification | recipient, actor, verb (reaction/comment/follow), reaction_type, target_post, target_user, is_read, created_at |

## URL Routes (feed/urls.py)
| Method | URL | View | Name |
|--------|-----|------|------|
| GET | `/` | feed | feed |
| GET/POST | `/register/` | register | register |
| GET/POST | `/login/` | LoginView | login |
| POST | `/logout/` | LogoutView | logout |
| POST | `/post/new/` | create_post | create_post |
| POST | `/post/<id>/delete/` | delete_post | delete_post |
| POST | `/post/<id>/comment/` | add_comment | add_comment |
| GET | `/post/<id>/react/?type=` | toggle_reaction | toggle_reaction |
| GET | `/profile/<username>/` | profile_view | profile |
| GET/POST | `/profile/<username>/edit/` | edit_profile | edit_profile |
| GET | `/profile/<username>/follow/` | toggle_follow | toggle_follow |
| GET | `/hashtag/<tag>/` | hashtag_posts | hashtag_posts |
| GET | `/search/?q=` | search_users | search |
| GET | `/load-more/?offset=` | load_more_posts | load_more_posts |
| GET | `/notifications/` | notification_list | notifications |
| GET | `/notifications/read/<id>/` | mark_notification_read | mark_notification_read |
| GET | `/notifications/unread-count/` | unread_notification_count | unread_notification_count |

## Views (feed/views.py)
- `register` - Create user + profile, redirect to login
- `feed` - Show latest 5 posts, user reactions, following IDs, unread count
- `create_post` - Create post with image, auto-parse hashtags
- `delete_post` - Delete own post
- `add_comment` - Add comment, create notification for post author
- `toggle_reaction` - Add/change/remove reaction, create notification
- `profile_view` - Show user profile, posts, follow stats
- `toggle_follow` - Follow/unfollow, create notification
- `edit_profile` - Edit avatar, cover, bio
- `hashtag_posts` - Show all posts with given hashtag
- `search_users` - AJAX search users + posts
- `load_more_posts` - AJAX infinite scroll pagination (5 per page)
- `notification_list` - Show all notifications
- `mark_notification_read` - AJAX mark single notification as read
- `unread_notification_count` - AJAX get unread count

## Templates
| Template | Extends | Purpose |
|----------|---------|---------|
| `base.html` | - | Main layout, navbar, dark mode, search, notification bell |
| `feed.html` | base | Feed page with create post, posts, reactions, infinite scroll |
| `_post.html` | - | Partial for rendering a single post (used by feed + load-more) |
| `profile.html` | base | User profile with cover, avatar, follow button, posts |
| `login.html` | base | Login form |
| `register.html` | base | Register form |
| `edit_profile.html` | base | Edit profile form |
| `notifications.html` | base | Notification list |

## Features Implemented
- [x] User registration + login/logout
- [x] Post creation with image upload
- [x] Post deletion (own only)
- [x] Comments on posts
- [x] 6 emoji reactions (hover popup): like, love, laugh, wow, sad, angry
- [x] Follow/unfollow users
- [x] Hashtag auto-detection (#word) + dedicated hashtag page
- [x] Live search (users + posts, debounced)
- [x] Infinite scroll (IntersectionObserver, 5 per page)
- [x] Notification system (reaction, comment, follow)
- [x] Dark mode toggle (CSS variables + localStorage)
- [x] Responsive design (Bootstrap 5)
- [x] Thai language UI + Prompt font
- [x] Profile page with cover photo + bio
- [x] Gradient theme + animations (fadeInUp, heartBeat)
- [x] Notification badge auto-refresh (15s)

## Known Issues / TODOs
1. Hashtag in post text is auto-parsed on save, but displayed as plain text (not linked) - could add a template filter to convert #tag to clickable links
2. Infinite scroll on hashtag page is disabled (shows all posts at once) - could add pagination
3. Post text doesn't have character count
4. No email verification / password reset
5. No admin dashboard for content moderation
6. Notifications don't navigate to source post (just marks as read)
7. Error messages UX could be improved (toast notifications)
8. No image preview/validation before upload
9. No loading skeleton/pulse animation
10. Test coverage is manual (no Django TestCase classes)

## Test Users
| Username | Password | Bio |
|----------|----------|-----|
| test | 12345678 | (original test user) |
| somsak | 123456 | ชอบเที่ยว ทะเล และกาแฟ |
| malai | 123456 | นักอ่านตัวยง รักแมว |
| prasert | 123456 | ช่างภาพสมัครเล่น |
| nong | 123456 | ชอบดูหนัง ฟังเพลง |
| somchai | 123456 | คนรักการทำอาหาร |

## Passed Tests (35/35)
Login, Register, Logout, Create/Delete post, Comment, Reaction (add/change/remove), Search (users + posts), Hashtag (found + 404), Profile, Follow/Unfollow, Notifications (display + mark read + unread count), Edit Profile, Load More, 404 handler, Feed integrity.
