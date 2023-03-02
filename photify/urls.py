from django.urls import path, re_path
from . import views
from django.contrib.auth.views import LoginView, PasswordResetConfirmView
from .tokens import password_reset_token
from django.urls import reverse_lazy

urlpatterns = [
    path('home/', views.home, name='homepage'),
    path('post/add-post/', views.add_post, name='add_post'),
    path('profile/<int:profile_id>/', views.view_profile, name='profile'),
    path('profile/follow-request/', views.send_follow_request, name='send_follow_request'),
    path('profile/follow-list/', views.follow_list, name='follow_list'),
    path('profile/search/', views.search_user, name='search_user'),
    path('images/post_images/<img_name>', views.get_post_image, name='get_post_image'),
    path('images/post_images/<img_name>/', views.get_post_image, name='get_post_image'),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_user, name='logout'),
    path('accounts/change_password/', views.change_password, name='change_password'),
    path('accounts/reset_password_request/', views.reset_password_request, name='reset_password_request'),
    path('accounts/reset/<uidb64>/<token>',
         PasswordResetConfirmView.as_view(template_name='registration/reset_password.html',
                                          token_generator=password_reset_token, success_url=reverse_lazy('login')),
         name='reset_password'),
    path('accounts/register/', views.register_user, name='register_user'),
    path('accounts/activate/<uidb64>/<token>', views.activate_account, name='activate_account'),
    path('accounts/follow-request-action/', views.follow_request_action, name='follow_request_action'),
    path('post/like/', views.like_post, name='like_post'),
]
