import re
from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse

register = template.Library()

EMOJI_MAP = {
    'like': '👍', 'love': '😍', 'laugh': '😂',
    'wow': '😮', 'sad': '😢', 'angry': '😡',
}

@register.filter
def get_item(d, key):
    return d.get(key)

@register.filter
def to_emoji(val):
    return EMOJI_MAP.get(val, '👍')

@register.filter(is_safe=True)
def hashtag_linkify(text):
    return mark_safe(re.sub(
        r'#(\w+)',
        r'<a href="/hashtag/\1/" class="hashtag-link">#\1</a>',
        str(text)
    ))

@register.filter(is_safe=True)
def mention_linkify(text):
    return mark_safe(re.sub(
        r'@(\w+)',
        r'<a href="/profile/\1/" class="hashtag-link">@\1</a>',
        str(text)
    ))
