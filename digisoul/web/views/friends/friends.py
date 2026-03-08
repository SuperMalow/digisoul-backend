# 每个用户与角色的关联关系的视图

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from web.models.Friends import Friends
from web.models.Character import Character
from web.serializers.friends.FriendsSerializers import FriendsSerializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView

# 获取或创建好友
class CreateFriendsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            me = request.user
            character_uuid = request.data.get('character_uuid')
            if not character_uuid:
                return Response({'result': 'error', 'message': '缺少 character_uuid'}, status=status.HTTP_400_BAD_REQUEST)
            character = Character.objects.filter(uuid=character_uuid).first()
            if not character:
                return Response({'result': 'error', 'message': '角色不存在'}, status=status.HTTP_404_NOT_FOUND)
            friends = Friends.objects.filter(character=character, me=me)
            if friends.exists():
                friend = friends.first()
            else:
                friend = Friends.objects.create(me=me, character=character)
            return Response({'result': 'success', 'message': '获取或创建好友成功', 'friend': FriendsSerializers(friend).data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'result': 'error', 'message': '系统异常，获取或创建好友失败', 'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 删除好友
class DeleteFriendsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            friend_uuid = request.data.get('friend_uuid')
            friend = Friends.objects.filter(uuid=friend_uuid, me=request.user)
            if not friend.exists():
                return Response({'result': 'error', 'message': '好友不存在'}, status=status.HTTP_404_NOT_FOUND)
            friend = friend.first()
            friend.delete()
            return Response({'result': 'success', 'message': '删除好友成功', 'friend': FriendsSerializers(friend).data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'result': 'error', 'message': '系统异常，删除好友失败', 'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 获取好友列表分页器
class FriendsPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 20

# 获取好友列表
class GetFriendsListView(ListAPIView):
    serializer_class = FriendsSerializers
    pagination_class = FriendsPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Friends.objects.filter(me=self.request.user).order_by('-created_at')
