# 角色与用户之间的聊天记录序列化器

from rest_framework import serializers
from web.models.Friends import Message

# 角色与用户之间的聊天记录序列化器
class MessageSerializers(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['uuid', 'friend', 'user_message', 'input', 'output', 'input_tokens', 'output_tokens', 'total_tokens', 'created_at']