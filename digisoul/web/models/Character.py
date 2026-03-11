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

class Character(models.Model):
    uuid = UUIDField(unique=True, auto=True, prefix='character', length=16)
    author = models.ForeignKey(DigisoulUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
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
