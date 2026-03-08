from web.models.Friends import Friends
from rest_framework import serializers
from web.serializers.user.account.AccountSerializers import UserSerializers
from web.serializers.character.CharacterSerializers import CharacterSerializers

class FriendsSerializers(serializers.ModelSerializer):
    character = CharacterSerializers()

    class Meta:
        model = Friends
        fields = ['uuid', 'character', 'created_at', 'updated_at']