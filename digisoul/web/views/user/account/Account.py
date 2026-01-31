# 用户账号相关视图
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from web.serializers.user.account.AccountSerializers import UserPasswordLoginSerializers, UserSerializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework.permissions import IsAuthenticated

# 用户密码登录
class UserPasswordLoginView(APIView):
    def post(self, request):
        serializer = UserPasswordLoginSerializers(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            response = Response({'result': 'success', 'user': UserSerializers(user).data, 'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_200_OK)
            print('cookie 过期时间：', settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(), '秒')
            response.set_cookie('refresh_token', str(refresh), httponly=True, samesite='Strict', max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
            return response
        return Response({'result': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 用户退出登录
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                except_message = 'refresh_token 无效或已过期，无法加入黑名单'
            else:
                except_message = 'refresh_token 加入黑名单成功'
        # 删去绑在 cookie 上的 refresh_token
        response = Response({'result': 'success', 'message': except_message}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        return response