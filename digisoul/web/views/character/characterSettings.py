from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from web.serializers.character.CharacterSerializers import CharacterSettingsSerializer
from web.models.Character import CharacterSettings

# 获取角色设置
class GetCharacterSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    # 获取角色设置信息
    def get(self, request):
        character_uuid = request.query_params.get('character_uuid')

        queryset = CharacterSettings.objects.all()
        if character_uuid:
            queryset = queryset.filter(character__uuid=character_uuid, character__author=request.user)

        character_settings = CharacterSettingsSerializer(queryset, many=True).data
        return Response({'result': 'success', 'character_settings': character_settings}, status=status.HTTP_200_OK)

# 更新角色设置信息
class UpdateCharacterSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    # 更新角色设置信息
    def post(self, request):
        uuid = request.data.get('uuid')
        if not uuid:
            return Response({'result': 'error', 'errors': {'uuid': ['请提供要更新的角色设置 uuid']}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            character_settings = CharacterSettings.objects.get(uuid=uuid, character__author=request.user)
        except CharacterSettings.DoesNotExist:
            return Response({'result': 'error', 'errors': {'uuid': ['角色设置不存在']}}, status=status.HTTP_404_NOT_FOUND)
        serializer = CharacterSettingsSerializer(instance=character_settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'result': 'success', 'character_settings': serializer.data}, status=status.HTTP_200_OK)
        return Response({'result': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)