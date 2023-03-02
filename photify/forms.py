from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Textarea
from django.utils import timezone
from .models import User, Post


class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=100, required=True)

    class Meta:
        model = User
        fields = {'username', 'email', 'password1', 'password2'}

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError({'username': ['Username is taken.', ]})
        elif User.objects.filter(email=email).exists():
            raise ValidationError({'email': ['Email is already in use.', ]})
        elif self.cleaned_data.get('password1') != self.cleaned_data.get('password2'):
            raise ValidationError({'password2': ['Passwords don\'t match.', ]})
        return self.cleaned_data


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = {'caption', 'image', 'private'}
        widgets = {
            'caption': Textarea(attrs={'cols': 60, 'rows': 6, 'id': 'post-form-caption-field',
                                       'placeholder': 'Write your post\'s caption here...'}),
        }

    def save(self, commit=True):
        post = super(PostForm, self).save(commit=False)
        post.published_date = timezone.now()
        if commit:
            post.save()
        return post
