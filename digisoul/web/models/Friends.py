# 每个用户与角色的关联关系
from django.db import models
from web.models.User import DigisoulUser
from web.models.Character import Character
from django.utils.timezone import localtime, now
from web.utils.CustomUUID import UUIDField

class Friends(models.Model):
    uuid = UUIDField(unique=True, auto=True, prefix='friend', length=16, max_length=30)
    me = models.ForeignKey(DigisoulUser, on_delete=models.CASCADE, related_name='me')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='character')
    memory = models.TextField(default='', max_length=10000, blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.me.username} - {self.character.name} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'digisoul friends'
        ordering = ['-created_at']