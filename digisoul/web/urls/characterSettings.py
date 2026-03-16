from django.urls import path
from web.views.character.characterSettings import GetCharacterSettingsView, UpdateCharacterSettingsView

urlpatterns = [
    # 获取角色设置信息
    path('get/', GetCharacterSettingsView.as_view(), name='get_character_settings'),
    # 更新角色设置信息
    path('update/', UpdateCharacterSettingsView.as_view(), name='update_character_settings'),
]