# character view
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from web.serializers.character.CharacterSerializers import (
    CharacterWriteSerializer,
    CharacterSerializers,
    CharacterListSerializers
)
from web.models.Character import Character
from web.utils.delete_old_photo import delete_old_photo
from rest_framework.pagination import PageNumberPagination
from web.models.User import DigisoulUser
from django.db.models import Q

# 更新角色信息（支持部分更新与完整更新，请求体需包含 uuid 指定要更新的角色）
class UpdateCharacterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        uuid = request.data.get('uuid')
        if not uuid:
            return Response(
                {'result': 'error', 'errors': {'uuid': ['请提供要更新的角色 uuid']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            character = Character.objects.get(uuid=uuid)
        except Character.DoesNotExist:
            return Response(
                {'result': 'error', 'errors': {'uuid': ['角色不存在']}},
                status=status.HTTP_404_NOT_FOUND
            )
        if character.author != request.user:
            return Response(
                {'result': 'error', 'errors': {'uuid': ['你不是该角色作者，无法更新']}},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CharacterWriteSerializer(
            instance=character,
            data=request.data,
            context={'request': request},
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({'result': 'success', 'character': serializer.data}, status=status.HTTP_200_OK)
        return Response({'result': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 创建角色
class CreateCharacterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CharacterWriteSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({'result': 'success', 'character': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'result': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 删除角色信息
class DeleteCharacterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            uuid = request.data.get('uuid')
            if not uuid:
                return Response({'result': 'error', 'message': '请提供角色 uuid'}, status=status.HTTP_400_BAD_REQUEST)
            character = Character.objects.get(uuid=uuid)
            if character.author != request.user:
                return Response({'result': 'error', 'message': '你不是该角色作者，无法删除该角色'}, status=status.HTTP_401_UNAUTHORIZED)
            # 删除角色关联的图片
            delete_old_photo(character.photo)
            delete_old_photo(character.background_photo)
            # 删除角色
            character.delete()
            return Response({'result': 'success', 'message': '角色删除成功', 'character': CharacterSerializers(character).data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'result': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 获取角色信息
class GetCharacterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        uuid = request.query_params.get('uuid')
        if not uuid:
            return Response({'result': 'error', 'errors': {'uuid': ['请提供角色 uuid']}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            character = Character.objects.get(uuid=uuid)
            if character.author != request.user:
                return Response({'result': 'error', 'errors': {'uuid': ['你不是该角色作者，无法获取该角色信息']}}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'result': 'success', 'character': CharacterSerializers(character).data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'result': 'error', 'errors': {'uuid': [str(e)]}}, status=status.HTTP_400_BAD_REQUEST)

# 分页器
class CharacterListPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 20

# 个人空间信息 - 通过用户 uuid 获取
class GetCharacterListView(ListAPIView):
    serializer_class = CharacterListSerializers
    pagination_class = CharacterListPagination
    def get_queryset(self):
        uuid = self.request.query_params.get('uuid')
        if not uuid:
            return Response({'result': 'error', 'message': 'uuid为空'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = DigisoulUser.objects.get(uuid=uuid)
        except DigisoulUser.DoesNotExist:
            return Response({'result': 'error', 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Character.objects.filter(author=user).order_by('-created_at')

# 个人空间信息 - 通过 user 获取
class GetCharacterListIndexView(ListAPIView):
    serializer_class = CharacterListSerializers
    pagination_class = CharacterListPagination

    def get_queryset(self):
        q = self.request.query_params.get('q')
        if q:
            return Character.objects.filter(Q(name__icontains=q) | Q(profile__icontains=q)).order_by('-created_at')
        return Character.objects.all().order_by('-created_at')