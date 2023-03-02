import os.path

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, HttpResponse
from django.http import HttpResponseForbidden, HttpResponseNotFound, FileResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .decorators import user_not_authenticated
from .models import Post, PostLikes, FollowRequest, Followers
from django.db.models import Q
from django.http import JsonResponse
from django_ajax.decorators import ajax
from django.contrib import messages
from .forms import RegisterForm, PostForm
import json

from .tokens import account_activation_token, password_reset_token

from itertools import chain


@login_required
def home(request, template='home.html', page_template='post.html'):
    followed = Followers.objects.filter(follower=request.user).values_list('user', flat=True)
    # first show posts from yourself and followed people
    posts_important = Post.objects.filter(Q(author=request.user) | Q(author__in=followed)).order_by(
        '-published_date').all()
    # then show public posts
    posts_public = Post.objects.filter(private=False).order_by('-published_date').all()
    posts = posts_important | posts_public
    for post in posts:
        post.likes = PostLikes.objects.filter(post_id=post.id).count()
        if PostLikes.objects.filter(user=request.user, post_id=post.id).exists():
            post.liked = True

    follow_requests = FollowRequest.objects.filter(user_to=request.user.id).filter(
        rejected_date__isnull=True).order_by('-sent_date').select_related('user_from').all()

    context = {'user': request.user, 'post_list': posts, 'follow_requests': follow_requests, 'post_form': PostForm,
               'page_template': page_template}

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        template = page_template

    return render(request, context=context, template_name=template)


@login_required
def get_post_image(request, img_name):
    try:
        post = Post.objects.get(image='post_images/' + img_name)
    except Post.DoesNotExist:
        return HttpResponseNotFound()

    if (not post.private) or (post.author == request.user) or (
            Followers.objects.filter(user=post.author, follower=request.user).exists()):
        return FileResponse(post.image)
    else:
        return HttpResponseForbidden()


@login_required
def view_profile(request, profile_id):
    profile = User.objects.get(id=profile_id)
    follower_count = Followers.objects.filter(user=profile).count()
    if request.user == profile:
        posts = Post.objects.filter(author=profile).all()
        follow_status = 'yourself'
    elif Followers.objects.filter(user=profile, follower=request.user).exists():
        posts = Post.objects.filter(author=profile).all()
        follow_status = 'followed'
    else:
        posts = Post.objects.filter(Q(author=profile) & Q(private=False)).all()
        try:
            fr = FollowRequest.objects.get(user_from=request.user, user_to_id=profile_id)
            print(fr.rejected_date)
            if fr.rejected_date is None:
                follow_status = 'pending'
            elif timezone.now() - fr.rejected_date > timezone.timedelta(
                    days=30):  # 30 days after reject, allow new requests
                fr.delete()
                follow_status = 'not sent'
            else:
                follow_status = 'rejected'
        except FollowRequest.DoesNotExist:
            follow_status = 'not sent'

    context = {'profile': profile, 'follower_count': follower_count, 'posts': posts, 'follow_status': follow_status}
    return render(request, context=context, template_name='profile.html')


@login_required
def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
    return redirect('homepage')


@user_not_authenticated(redirect_url='homepage')
def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_activation_email(request, user, user.email)
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, context={'form': form}, template_name='registration/register.html')


def send_activation_email(request, user, to_email):
    mail_subject = 'Activate your photify account'
    message = render_to_string('registration/activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request,
                         'Check your email for the activation email and click the link to complete the registration.')
    else:
        messages.error(request, f'Problem sending confirmation email to {to_email}, check if you typed it correctly.')


@user_not_authenticated(redirect_url='homepage')
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, 'Account activated. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
    return redirect('login')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.clean_old_password()
            form.save()
            messages.success(request, 'Password changed successfully! Please log in.')
            logout(request)
            return redirect('login')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, context={'form': form}, template_name='registration/change_password.html')


def send_reset_email(request, user, to_email):
    mail_subject = 'Reset your photify password'
    message = render_to_string('registration/reset_password_email.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': password_reset_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request,
                         'Instructions on how to reset the password were sent to the entered email, '
                         'if there exists an account linked to it')
    else:
        messages.error(request, f'Problem sending confirmation email to {to_email}, check if you typed it correctly.')


@user_not_authenticated(redirect_url='change_password')
def reset_password_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            try:
                user = next(form.get_users(form.cleaned_data['email']))
            except StopIteration:
                user = None
            if user:
                send_reset_email(request, user, form.cleaned_data['email'])
            else:
                messages.error(request, 'No account linked to this email address')
    form = PasswordResetForm()
    return render(request, context={'form': form}, template_name='registration/reset_password_request.html')


def logout_user(request):
    logout(request)
    return redirect('login')


def get_like_count(post_id):
    likes = PostLikes.objects.filter(post_id=post_id).count()
    data = {
        "likesCount": likes
    }
    return JsonResponse(data)


@ajax
@login_required
def like_post(request):
    post_data = json.load(request)['post_data']
    if post_data['action'] == 'like':
        if PostLikes.objects.filter(user_id=post_data['user_id'], post_id=post_data['post_id']).exists():
            response = JsonResponse({'error': 'The user has already liked this post'})
            response.status_code = 409
            return response
        else:
            PostLikes(post_id=post_data['post_id'], user_id=post_data['user_id']).save()
            return get_like_count(post_data['post_id'])
    elif post_data['action'] == 'unlike':
        if PostLikes.objects.filter(user_id=post_data['user_id'], post_id=post_data['post_id']).exists():
            PostLikes.objects.get(post_id=post_data['post_id'], user_id=post_data['user_id']).delete()
            return get_like_count(post_data['post_id'])
        else:
            response = JsonResponse({'error': 'The user cannot unlike a post, that he has not liked'})
            response.status_code = 409
            return response

    response = JsonResponse({'error': 'Incorrect request action'})
    response.status_code = 400
    return response


@ajax
@login_required
def follow_request_action(request):
    post_data = json.load(request)['post_data']
    if post_data['action'] == 'accept':
        Followers(user_id=post_data['user_to_id'], follower_id=post_data['user_from_id'],
                  date_from=timezone.now()).save()
        FollowRequest.objects.get(user_from=post_data['user_from_id'], user_to=post_data['user_to_id']).delete()
        return JsonResponse({'status': 'succes'})
    elif post_data['action'] == 'reject':
        fr = FollowRequest.objects.get(user_from=post_data['user_from_id'], user_to=post_data['user_to_id'])
        fr.rejected_date = timezone.now()
        fr.save()
        return JsonResponse({'status': 'success'})

    response = JsonResponse({'error': 'Incorrect request action'})
    response.status_code = 400
    return response


@ajax
@login_required
def send_follow_request(request):
    post_data = json.load(request)['post_data']
    profile_id = post_data['profile_id']
    action = post_data['action']
    if action == 'follow':
        if (not FollowRequest.objects.filter(user_from=request.user, user_to_id=profile_id).exists()) and \
                (not Followers.objects.filter(user_id=profile_id, follower=request.user).exists()):
            FollowRequest(user_from=request.user, user_to_id=profile_id, sent_date=timezone.now()).save()
            return JsonResponse({'status': 'success'})
    else:
        try:
            follow = Followers.objects.get(user_id=profile_id, follower=request.user)
            follow.delete()
            return JsonResponse({'status': 'success'})
        except Followers.DoesNotExist:
            jr = JsonResponse({'error': 'Impossible action'})
            jr.status_code = 409
            return jr


@ajax
@login_required
def search_user(request):
    post_data = json.load(request)['post_data']
    username = post_data['username']
    try:
        user_id = User.objects.get(username=username).id
        return JsonResponse({'redirect_url': redirect('profile', profile_id=user_id).url})
    except User.DoesNotExist:
        jr = JsonResponse({'error': 'No such user found'})
        jr.status_code = 204
        return jr


@login_required
def follow_list(request):
    followed = Followers.objects.filter(follower=request.user).select_related('follower').order_by('-date_from').all()
    followers = Followers.objects.filter(user=request.user).select_related('user').order_by('-date_from').all()
    context = {'followed': followed, 'followers': followers}
    return render(request, context=context, template_name='follow_list.html')
