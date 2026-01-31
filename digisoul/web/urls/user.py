from django.urls import path
from web.views.user.account.Account import UserPasswordLoginView, UserLogoutView

urlpatterns = [
    path('password/login/', UserPasswordLoginView.as_view(), name='user_password_login'),
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
]