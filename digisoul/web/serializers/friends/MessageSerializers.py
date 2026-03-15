# 角色与用户之间的聊天记录序列化器

from rest_framework import serializers
from web.models.Friends import Message
from web.serializers.friends.FriendsSerializers import FriendsSerializers

# 获取历史消息序列化器
class HistoryMessageSerializers(serializers.ModelSerializer):
    friend_uuid = serializers.SerializerMethodField(read_only=True)
    
    def get_friend_uuid(self, obj):
        return obj.friend.uuid if obj.friend else None

    class Meta:
        model = Message
        fields = ['uuid', 'friend_uuid', 'user_message', 'audio_message', 'tts_audio', 'output', 'created_at']