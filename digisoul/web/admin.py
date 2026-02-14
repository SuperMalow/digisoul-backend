from django.contrib import admin
from .models.User import DigisoulUser
from django.contrib.auth.admin import UserAdmin
from web.models.Character import Character

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
    raw_id_fields = ('author',)
    list_display = ('uuid', 'name', 'author', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('uuid', 'name', 'author__username')
    ordering = ('-created_at',)
    list_per_page = 20
    list_max_show_all = 100
    list_display_links = ('uuid', 'name', 'author')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)