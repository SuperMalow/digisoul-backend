from email.policy import default
from django.db import models
import shortuuid
from web.models.User import DigisoulUser
from django.utils.timezone import localtime, now
from django.core.validators import FileExtensionValidator, validate_image_file_extension
import os
from django.core.exceptions import ValidationError
from web.utils.CustomUUID import UUIDField

def photo_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{shortuuid.uuid()[:20]}{ext}"
    return f"characters/photos/{new_name}"

def background_photo_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{shortuuid.uuid()[:20]}{ext}"
    return f"characters/backgrounds/{new_name}"

def validate_photo_size(file):
    # 限制头像大小（默认 4MB）
    max_bytes = 4 * 1024 * 1024
    if getattr(file, "size", 0) > max_bytes:
        raise ValidationError(f"图片大小不能超过 {max_bytes // (1024 * 1024)}MB")

def validate_background_photo_size(file):
    # 限制背景图片大小（默认 8MB）
    max_bytes = 8 * 1024 * 1024
    if getattr(file, "size", 0) > max_bytes:
        raise ValidationError(f"背景图片大小不能超过 {max_bytes // (1024 * 1024)}MB")

# 虚拟角色ORM模型
class Character(models.Model):
    # 定义性别
    GENDER_TYPES = [
        ('male', '男'),
        ('female', '女'),
    ]
    uuid = UUIDField(unique=True, auto=True, prefix='character', length=16)
    author = models.ForeignKey(DigisoulUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=100, default='male', verbose_name="性别", choices=GENDER_TYPES)
    photo = models.ImageField(upload_to=photo_upload_to, validators=[
        validate_image_file_extension,
        FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]),
        validate_photo_size
        ])
    profile = models.TextField(max_length=100000)
    background_photo = models.ImageField(upload_to=background_photo_upload_to, validators=[
        validate_image_file_extension,
        FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]),
        validate_background_photo_size
            ])
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.author.username} - {self.name} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'digisoul character'
        ordering = ['-created_at']

# 角色扩展设置表
class CharacterSettings(models.Model):
    uuid = UUIDField(unique=True, auto=True, prefix='character_settings', length=16)
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='character_settings', to_field='uuid')
    voice = models.ForeignKey('CharacterVoice', on_delete=models.CASCADE, related_name='character_voice', to_field='uuid')
    is_public = models.BooleanField(default=True, verbose_name="是否公开")
    short_profile = models.CharField(max_length=100, default='', blank=True, null=True, verbose_name="角色简介")
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.character.name} - {self.voice.voice_name} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'digisoul character settings'
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

# 角色音色
class CharacterVoice(models.Model):
    # 定义音色语言
    LANGUAGE_CHOICES = [
        ('zh', '中文'),
        ('en', '英文'),
        ('ja', '日文'),
        ('ko', '韩文'),
    ]
    uuid = UUIDField(unique=True, auto=True, prefix='character_voice', length=16)
    voice_name = models.CharField(max_length=100, default='', verbose_name="音色名称") # 音色名称
    voice_types = models.CharField(max_length=100, default='', verbose_name="音色类型") # 音色类型
    voice_speed = models.FloatField(default=1.0, verbose_name="语速") # 语速
    voice_pitch = models.FloatField(default=1.0, verbose_name="音调") # 音调
    voice_volume = models.FloatField(default=50, verbose_name="音量") # 音量
    voice_style = models.CharField(max_length=100, default='', verbose_name="音色风格") # 音色风格
    voice_emotion = models.CharField(max_length=100, default='', verbose_name="音色情感") # 音色情感
    voice_language = models.CharField(max_length=100, default='zh', verbose_name="音色语言", choices=LANGUAGE_CHOICES) # 音色语言
    preview_voice = models.FileField(upload_to=audio_upload_to, validators=[
        validate_audio_file_extension,
        FileExtensionValidator(allowed_extensions=["mp3", "m4a"]),
    ], verbose_name='TTS语音文件', default=None, null=True, blank=True)  # 试听语音
    preview_text = models.CharField(max_length=100, default='你好，请问有什么事情嘛？', verbose_name="试听文本") # 试听文本
    
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.voice_language} - {self.voice_name} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"