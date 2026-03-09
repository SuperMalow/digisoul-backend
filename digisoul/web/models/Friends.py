# 每个用户与角色的关联关系
from django.db import models
from web.models.User import DigisoulUser
from web.models.Character import Character
from django.utils.timezone import localtime, now
from web.utils.CustomUUID import UUIDField

# 记录角色与用户之间的关系
class Friends(models.Model):
    uuid = UUIDField(unique=True, auto=True, prefix='friend', length=16, max_length=30)
    me = models.ForeignKey(DigisoulUser, on_delete=models.CASCADE, related_name='me', to_field='uuid')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='character', to_field='uuid')
    memory = models.TextField(default='', max_length=10000, blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.me.username} - {self.character.name} - {localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'digisoul friends'
        ordering = ['-created_at']

# 记录角色与用户之间的聊天记录
class Message(models.Model):
    friend = models.ForeignKey(Friends, on_delete=models.CASCADE, related_name='friend', to_field='uuid') # 直接记录角色和用户
    user_message = models.TextField(default='', max_length=10000, blank=True, null=True) # 用户发送的消息
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