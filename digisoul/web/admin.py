from django.contrib import admin
from .models.User import DigisoulUser
from django.contrib.auth.admin import UserAdmin

# admin.site.register(DigisoulUser, UserAdmin)
@admin.register(DigisoulUser)
class DigisoulUserAdmin(UserAdmin):
    # raw_id_fields 用于显示关联字段 提高性能 会以分页方式显示
    raw_id_fields = ('groups', 'user_permissions')
    list_display = ('uuid',  'username', 'email', 'is_active', 'is_staff', 'last_login_at')