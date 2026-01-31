from django.urls import path
from web.views.user.account.Token import UserTokenRefreshView, UserTokenRefreshViewV2

urlpatterns = [
    path('refresh/', UserTokenRefreshView.as_view(), name='user_token_refresh'),
    # 采用rest_framework_simplejwt.serializers.TokenRefreshSerializer 刷新token
    # path('refresh-v2/', UserTokenRefreshViewV2.as_view(), name='user_token_refresh_v2'),
]