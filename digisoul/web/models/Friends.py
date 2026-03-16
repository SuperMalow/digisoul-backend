# 每个用户与角色的关联关系
from django.db import models
from langchain_core.load.dump import default
from web.models.User import DigisoulUser
from web.models.Character import Character
from django.utils.timezone import localtime, now
from web.utils.CustomUUID import UUIDField
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os
import shortuuid

# 记录角色与用户之间的关系
class Friends(models.Model):
    uuid = UUIDField(unique=True, auto=True, prefix='friend', length=16, max_length=30)
    me = models.ForeignKey(DigisoulUser, on_delete=models.CASCADE, related_name='me', to_field='uuid')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='character', to_field='uuid')
    memory = models.TextField(default='', max_length=10000, blank=True, null=True)

    # 角色与用户的好感度
    intimacy_score = models.IntegerField(default=0, blank=True, null=True,verbose_name="好感度/亲密度")

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.me.username} - {self.character.name} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'digisoul friends'
        ordering = ['-created_at']

# 语音上传
def audio_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{shortuuid.uuid()[:20]}{ext}"
    return f"audio/messages/{new_name}"

# 验证语音文件拓展名
def validate_audio_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()  # 获取文件扩展名
    valid_extensions = ['.mp3', '.wav', '.m4a', '.pcm']
    if not ext.lower() in valid_extensions:
        raise ValidationError('不支持的文件格式。')

# 记录角色与用户之间的聊天记录
class Message(models.Model):
    uuid = UUIDField(unique=True, auto=True, prefix='message', length=16, max_length=30)
    friend = models.ForeignKey(Friends, on_delete=models.CASCADE, related_name='friend', to_field='uuid') # 直接记录角色和用户
    user_message = models.TextField(default='', max_length=5000, blank=True, null=True) # 用户发送的消息
    audio_message = models.FileField(upload_to=audio_upload_to, validators=[
        validate_audio_file_extension,
        FileExtensionValidator(allowed_extensions=["mp3", "m4a"]),
    ], verbose_name='语音文件', default=None, null=True, blank=True) # 用户的语音文件
    tts_audio = models.FileField(upload_to=audio_upload_to, validators=[
        validate_audio_file_extension,
        FileExtensionValidator(allowed_extensions=["mp3", "m4a"]),
    ], verbose_name='TTS语音文件', default=None, null=True, blank=True) # AI 的 TTS 语音回复
    input = models.TextField(default='', max_length=10000, blank=True, null=True) # 角色输入的消息
    output = models.TextField(default='', max_length=10000, blank=True, null=True) # 角色输出的消息
    input_tokens = models.IntegerField(default=0) # 输入的token数
    output_tokens = models.IntegerField(default=0) # 输出的token数
    total_tokens = models.IntegerField(default=0) # 总token数
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.friend.character.name} - {self.friend.me.username} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'user and character message'
        ordering = ['-created_at']