from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from web.serializers.character.CharacterSerializers import CharacterVoiceSerializer
from web.models.Character import CharacterVoice

# 角色音色列表
class GetCharacterVoiceView(APIView):
    permission_classes = [IsAuthenticated]

    # 获取角色音色列表
    def get(self, request):
        character_voices = CharacterVoice.objects.all()
        return Response({'result': 'success', 'character_voices': CharacterVoiceSerializer(character_voices, many=True).data}, status=status.HTTP_200_OK)

# 更新角色音色信息
class UpdateCharacterVoiceView(APIView):
    permission_classes = [IsAuthenticated]

    # 更新角色音色列表
    def post(self, request):
        uuid = request.data.get('uuid')
        if not uuid:
            return Response({'result': 'error', 'errors': {'uuid': ['请提供要更新的角色音色 uuid']}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            character_voice = CharacterVoice.objects.get(uuid=uuid)
        except CharacterVoice.DoesNotExist:
            return Response({'result': 'error', 'errors': {'uuid': ['角色音色不存在']}}, status=status.HTTP_404_NOT_FOUND)
        serializer = CharacterVoiceSerializer(instance=character_voice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'result': 'success', 'character_voice': serializer.data}, status=status.HTTP_200_OK)
        return Response({'result': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)