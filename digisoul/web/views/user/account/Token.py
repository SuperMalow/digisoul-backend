# 用户token相关视图
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.conf import settings

# 用户token刷新
class UserTokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'result': 'error', 'errors': 'refresh_token 不存在'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            return Response({'result': 'error', 'errors': 'refresh_token 已过期或无效'}, status=status.HTTP_401_UNAUTHORIZED)

        # 生成新的 access
        access = str(refresh.access_token)
        response = Response(
            {'result': 'success', 'message': 'token 刷新成功', 'access': access},
            status=status.HTTP_200_OK
        )

        # 旋转 refresh：下发新的 refresh_token；如启用 blacklisting，尽量拉黑旧 refresh_token
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION'):
                try:
                    refresh.blacklist()
                    print('refresh_token 加入黑名单成功')
                except Exception:
                    print('refresh_token 加入黑名单失败,可能未安装 token_blacklist app')

            refresh.set_jti()
            refresh.set_iat()
            refresh.set_exp()

            response.set_cookie(
                'refresh_token',
                str(refresh),
                httponly=True,
                samesite='Strict',
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            )

        return response

# 用户token刷新 v2
class UserTokenRefreshViewV2(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'result': 'error', 'errors': 'refresh_token 不存在'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            return Response({'result': 'error', 'errors': 'refresh_token 已过期或无效'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        if serializer.is_valid():
            access = str(refresh.access_token)
            response = Response(
                {'result': 'success', 'message': 'token 刷新成功', 'access': access},
                status=status.HTTP_200_OK
            )
            response.set_cookie('refresh_token', str(refresh), httponly=True, samesite='Strict', max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
            return response
        return Response({'result': 'error', 'errors': serializer.errors}, status=status.HTTP_401_UNAUTHORIZED)