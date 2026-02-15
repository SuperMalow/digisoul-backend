from django.db.models import CharField, EmailField, ImageField, DateTimeField, TextField
import shortuuid
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import localtime
import os
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, validate_image_file_extension

# custome uuid field
class UUIDField(CharField):
    def __init__(self, auto=True, *args, **kwargs):
        self.auto = auto
        self.prefix = kwargs.pop('prefix', '')
        self.length = kwargs.pop('length', 32)
        if auto:
            # 如果uuid是自动生成的，则不要让用户编辑
            kwargs['editable'] = False
            kwargs['blank'] = False
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = super(UUIDField, self).pre_save(model_instance, add)
        if self.auto and not value:
            value = shortuuid.uuid()
            # 处理长度限制
            if self.length:
                value = value[:self.length]
            # 添加前缀
            if self.prefix:
                value = f"{self.prefix}_{value}"
            setattr(model_instance, self.attname, value)
        return value

# 修改上传图片的保存路径并重命名
def photo_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()  # ".png"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".png"
    new_name = f"{shortuuid.uuid()[:20]}{ext}"
    return f"user/photos/{new_name}"

# 验证上传图片的大小
def validate_photo_size(file):
    # 限制头像大小（默认 4MB）
    max_bytes = 4 * 1024 * 1024
    if getattr(file, "size", 0) > max_bytes:
        raise ValidationError(f"图片大小不能超过 {max_bytes // (1024 * 1024)}MB")

# DigisoulUser model
class DigisoulUser(AbstractUser):
    uuid = UUIDField(unique=True, auto=True, prefix='user', length=16)
    email = EmailField(unique=True, null=False, blank=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    last_login_at = DateTimeField(null=True, blank=True)
    photo = ImageField(
        default='user/photos/defaultUserPhoto.jpeg',
        upload_to=photo_upload_to,
        validators=[
            validate_image_file_extension,
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]),
            validate_photo_size,
        ],
    )
    profile = TextField(default='谢谢关注喵~', max_length=500)
    
    # 指定用哪个字段作为用户的唯一身份标识
    USERNAME_FIELD = 'email' # 改为 email 登录
    # 在使用 createsuperuser命令创建超级用户时，提示输入的必填字段列表
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = 'digisoul user'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.username} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

