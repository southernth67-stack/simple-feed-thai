from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Comment, Profile, Message, Poll, PollOption


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'image']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'คุณกำลังคิดอะไรอยู่...', 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'เขียนความคิดเห็น...', 'class': 'form-control'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'cover_image', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'แนะนำตัวหน่อย...', 'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_image(self, field):
        img = self.cleaned_data.get(field)
        if img:
            if img.size > 5 * 1024 * 1024:
                raise forms.ValidationError('ไฟล์รูปต้องมีขนาดไม่เกิน 5MB')
            if img.content_type not in ['image/jpeg', 'image/png']:
                raise forms.ValidationError('รองรับเฉพาะไฟล์ JPEG และ PNG เท่านั้น')
        return img

    def clean_avatar(self):
        return self.clean_image('avatar')

    def clean_cover_image(self):
        return self.clean_image('cover_image')


class EditPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'image']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'พิมพ์ข้อความ...', 'class': 'form-control'}),
        }


class PollForm(forms.Form):
    question = forms.CharField(max_length=300, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'คำถามของคุณ...'
    }))
    option1 = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control mb-1', 'placeholder': 'ตัวเลือก 1'
    }))
    option2 = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control mb-1', 'placeholder': 'ตัวเลือก 2'
    }))
    option3 = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control mb-1', 'placeholder': 'ตัวเลือก 3 (ไม่จำเป็น)'
    }))
    option4 = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control mb-1', 'placeholder': 'ตัวเลือก 4 (ไม่จำเป็น)'
    }))
