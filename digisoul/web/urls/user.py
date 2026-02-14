from django.urls import path
from web.views.user.account.Account import UserPasswordLoginView, UserLogoutView, UserInfoView
from web.views.user.profile.UserProfile import UpdateUserProfileView

urlpatterns = [
    path('password/login/', UserPasswordLoginView.as_view(), name='user_password_login'),
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
    path('info/', UserInfoView.as_view(), name='user_info'),

    # 用户简介
    path('profile/update/', UpdateUserProfileView.as_view(), name='update_user_profile'),
]