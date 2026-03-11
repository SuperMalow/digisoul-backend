from django.contrib import admin
from .models.User import DigisoulUser
from django.contrib.auth.admin import UserAdmin
from web.models.Character import Character
from web.models.Friends import Friends, Message
from web.models.Prompt import SystemPrompt

@admin.register(DigisoulUser)
class DigisoulUserAdmin(UserAdmin):
    # raw_id_fields 用于显示关联字段 提高性能 会以分页方式显示
    raw_id_fields = ('groups', 'user_permissions')
    list_display = ('uuid',  'username', 'email', 'is_active', 'is_staff', 'last_login_at')
    list_filter = ('is_active', 'is_staff', 'last_login_at')
    search_fields = ('username', 'email')
    ordering = ('-last_login_at',)
    list_per_page = 20
    list_max_show_all = 100
    list_display_links = ('uuid', 'username', 'email')
    list_filter = ('is_active', 'is_staff', 'last_login_at')
    search_fields = ('username', 'email')
    ordering = ('-last_login_at',)
    
    fieldsets = (
        ['基本信息',{
            'fields': ('username', 'email', 'password', 'is_active', 'is_staff', 'last_login_at', 'date_joined'),
        }],
        ['更多信息',{
            'fields': ('profile', 'photo'),
        }],
    )

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    raw_id_fields = ('author',) # 关联字段 提高性能 会以分页方式显示
    list_display = ('uuid', 'name', 'author', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('uuid', 'name', 'author__username')
    ordering = ('-created_at',)
    list_per_page = 20
    list_max_show_all = 100
    list_display_links = ('uuid', 'name', 'author')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(Friends)
class FriendsAdmin(admin.ModelAdmin):
    raw_id_fields = ('me', 'character') # 关联字段 提高性能 会以分页方式显示
    list_display = ('uuid', 'me', 'character', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('me__username', 'character__name')
    ordering = ('-created_at',)
    list_per_page = 20
    list_max_show_all = 100
    list_display_links = ('uuid', 'me', 'character')
    ordering = ('-created_at',)

@admin.register(Message)
class messageAdmin(admin.ModelAdmin):
    raw_id_fields = ('friend',) # 关联字段 提高性能 会以分页方式显示
    list_display = ('friend__uuid', 'friend', 'input_tokens', 'output_tokens', 'total_tokens', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('friend__me__username', 'friend__character__name')
    ordering = ('-created_at',)
    list_per_page = 20
    list_max_show_all = 100
    list_display_links = ('friend__uuid', 'friend')
    ordering = ('-created_at',)

@admin.register(SystemPrompt)
class SystemPromptAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'title', 'order_number', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'order_number')
    ordering = ('-created_at',)
    list_per_page = 20
    list_max_show_all = 100
    list_display_links = ('uuid', 'title', 'order_number')
    ordering = ('-created_at',)