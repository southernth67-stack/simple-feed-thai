import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_feed.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from feed.models import Profile

users_data = [
    ('somsak', 'สายชิล', 'somsak@example.com'),
    ('malai', 'สายแซ่บ', 'malai@example.com'),
    ('prasert', 'สายลุย', 'prasert@example.com'),
    ('nong', 'น้องใหม่', 'nong@example.com'),
    ('somchai', 'เพื่อนซี้', 'somchai@example.com'),
]

for username, display, email in users_data:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, email=email, password='123456')
        Profile.objects.get_or_create(user=user, defaults={'bio': f'สวัสดี ฉัน{display}'})
        print(f'✅ Created: {username} (pw: 123456)')
    else:
        print(f'⏭️  Exists: {username}')
