from django.db import models
from web.utils.CustomUUID import UUIDField
from django.utils.timezone import localtime, now

# 系统提示词记录数据库
class SystemPrompt(models.Model):
    uuid = UUIDField(unique=True, auto=True, prefix='system_prompt', length=16, max_length=30)
    title = models.CharField(max_length=255, default='', blank=True, null=True)
    order_number = models.IntegerField(default=0, blank=True, null=True) # 为了防止prompt太长，直接按照顺序继续拼接即可
    prompt = models.TextField(default='', max_length=10000, blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.uuid} - {self.title} - {self.prompt[:30]} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'system prompt'
        ordering = ['-created_at']