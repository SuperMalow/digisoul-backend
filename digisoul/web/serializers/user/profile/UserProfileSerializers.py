# 用户简介相关序列化器

from rest_framework import serializers
from web.models.User import DigisoulUser
from web.serializers.user.account.AccountSerializers import UserSerializers

# 更新用户简介序列化器
class UpdateUserProfileSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    profile = serializers.CharField(required=False, max_length=500)
    photo = serializers.ImageField(required=False)

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.profile = validated_data.get('profile', instance.profile)
        instance.photo = validated_data.get('photo', instance.photo)
        instance.save()
        return instance