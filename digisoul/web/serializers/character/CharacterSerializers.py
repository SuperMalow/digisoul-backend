# character related serializers
from rest_framework import serializers
from web.models.Character import Character
from web.serializers.user.account.AccountSerializers import UserSerializers


# character 获取信息序列化器
class CharacterSerializers(serializers.ModelSerializer):
    author = UserSerializers()

    class Meta:
        model = Character
        fields = ('uuid', 'name', 'photo', 'background_photo', 'profile', 'author', 'updated_at')

# character 创建/更新序列化器（统一处理创建与更新，根据是否传入 instance 自动区分）
class CharacterWriteSerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    name = serializers.CharField(required=False, max_length=100)
    photo = serializers.ImageField(required=False)
    background_photo = serializers.ImageField(required=False)
    profile = serializers.CharField(required=False, max_length=100000)

    def validate(self, attrs):
        # 创建时必须有 name, photo, background_photo, profile
        if not self.instance:
            for field in ('name', 'photo', 'background_photo', 'profile'):
                if field not in attrs:
                    raise serializers.ValidationError({field: ['创建角色时此字段必填']})
        return attrs

    def create(self, validated_data):
        author = self.context['request'].user
        return Character.objects.create(author=author, **validated_data)

    def update(self, instance, validated_data):
        if 'name' in validated_data:
            instance.name = validated_data['name']
        if 'profile' in validated_data:
            instance.profile = validated_data['profile']
        if 'photo' in validated_data:
            old_photo = instance.photo
            instance.photo = validated_data['photo']
            if old_photo and old_photo != instance.photo:
                old_photo.delete(save=False)
        if 'background_photo' in validated_data:
            old_bg = instance.background_photo
            instance.background_photo = validated_data['background_photo']
            if old_bg and old_bg != instance.background_photo:
                old_bg.delete(save=False)
        instance.save()
        return instance

# character 列表序列化器
class CharacterListSerializers(serializers.ModelSerializer):
    is_friend = serializers.SerializerMethodField(read_only=True)
    author = serializers.SerializerMethodField(read_only=True)

    def get_author(self, obj):
        return UserSerializers(obj.author).data if obj.author_id else None

    def get_is_friend(self, obj):
        from web.models.Friends import Friends
        from web.serializers.friends.FriendsSerializers import FriendsWriteSerializers
        # 查询friends表,判断是否存在当前用户的好友关系
        user = self.context['request'].user
        friend = Friends.objects.filter(character=obj, me=user).first()
        # print('friend: ', friend);
        return FriendsWriteSerializers(friend).data if friend else None

    class Meta:
        model = Character
        fields = ('uuid', 'name', 'photo', 'background_photo', 'profile', 'created_at', 'is_friend', 'author')
        
