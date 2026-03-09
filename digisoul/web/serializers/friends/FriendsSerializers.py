from web.models.Friends import Friends
from rest_framework import serializers
from web.serializers.user.account.AccountSerializers import UserSerializers
from web.serializers.character.CharacterSerializers import CharacterSerializers

# 是否为好友的序列化器
class FriendsWriteSerializers(serializers.ModelSerializer):
    me_uuid = serializers.SerializerMethodField(read_only=True)

    def get_me_uuid(self, obj):
        return obj.me.uuid if obj.me_id else None

    class Meta:
        model = Friends
        fields = ['uuid', 'me_uuid', ]

# 好友列表序列化器
class FriendsSerializers(serializers.ModelSerializer):
    character = CharacterSerializers()

    class Meta:
        model = Friends
        fields = ['uuid', 'character', 'memory', 'created_at', 'updated_at']
    