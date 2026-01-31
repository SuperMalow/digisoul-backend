# 用户账号相关序列化器
from rest_framework import serializers
from web.models.User import DigisoulUser

# 用户信息序列化器
class UserSerializers(serializers.ModelSerializer):

    class Meta:
        model = DigisoulUser
        # fields = '__all__'
        fields = ['uuid', 'username', 'email', 'photo', 'profile']

# 用户密码登录序列化器
class UserPasswordLoginSerializers(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = DigisoulUser.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError('邮箱不存在')
        if not user.check_password(password):
            raise serializers.ValidationError('邮箱或密码错误')
        attrs['user'] = user
        return attrs

