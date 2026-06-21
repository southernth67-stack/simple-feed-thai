from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        return {'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()}
    return {'unread_count': 0}
