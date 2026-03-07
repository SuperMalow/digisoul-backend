# 用户简介相关 views

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from web.serializers.user.profile.UserProfileSerializers import UpdateUserProfileSerializer
from web.serializers.user.account.AccountSerializers import UserSerializers
from web.models.User import DigisoulUser

# 更新用户简介
class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        serializer = UpdateUserProfileSerializer(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'result': 'success', 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response({'result': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 获取用户简介
class GetUserProfileView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        uuid = request.query_params.get('uuid')
        if not uuid:
            return Response({'result': 'error', 'message': 'uuid为空'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = DigisoulUser.objects.get(uuid=uuid)
        except DigisoulUser.DoesNotExist:
            return Response({'result': 'error', 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializers(instance=user)
        return Response({'result': 'success', 'message': '获取用户简介成功', 'user': serializer.data}, status=status.HTTP_200_OK)
