#!/usr/bin/env python3
"""Deploy simple-feed-thai to PythonAnywhere - run this from PA Bash console."""
import os
import subprocess
import sys

USER = os.environ.get('USER', os.environ.get('USERNAME', ''))
if not USER:
    print("❌ Cannot detect PythonAnywhere username")
    sys.exit(1)

REPO = 'https://github.com/southernth67-stack/simple-feed-thai.git'
PROJECT_DIR = os.path.expanduser(f'~/{USER}.pythonanywhere.com')
DOMAIN = f'{USER}.pythonanywhere.com'

steps = [
    ('Cloning repo', f'git clone {REPO} {PROJECT_DIR}'),
    ('Creating virtualenv', f'python -m venv {PROJECT_DIR}/venv'),
    ('Installing dependencies', f'{PROJECT_DIR}/venv/bin/pip install -r {PROJECT_DIR}/requirements.txt'),
    ('Running migrations', f'cd {PROJECT_DIR} && {PROJECT_DIR}/venv/bin/python manage.py migrate'),
    ('Collecting static files', f'cd {PROJECT_DIR} && {PROJECT_DIR}/venv/bin/python manage.py collectstatic --noinput'),
]

print(f'🚀 Deploying simple-feed-thai for user: {USER}')
print(f'📁 Project dir: {PROJECT_DIR}')
print(f'🌐 Domain: {DOMAIN}')
print()

for label, cmd in steps:
    print(f'⏳ {label}...')
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ⚠️  {r.stderr.strip()}')
    else:
        print(f'  ✅ OK')

print()
print('✅ Code deployed! Now go to the Web tab and:')
print(f'  1. Add a new web app → Manual config → Python 3.10')
print(f'  2. Set Source code: {PROJECT_DIR}')
print(f'  3. Set Working directory: {PROJECT_DIR}')
print(f'  4. Set Virtualenv: {PROJECT_DIR}/venv')
print(f'  5. Edit WSGI file to point to simple_feed.wsgi.application')
print(f'  6. Add static files:')
print(f'     /static/  →  {PROJECT_DIR}/staticfiles')
print(f'     /media/   →  {PROJECT_DIR}/media')
print(f'  7. Reload')
print(f'  🎉 Done! https://{DOMAIN}')
