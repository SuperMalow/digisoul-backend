from django.urls import path
from web.views.character.characterVoice import GetCharacterVoiceView, UpdateCharacterVoiceView

urlpatterns = [
    # 获取角色音色列表
    path('get/', GetCharacterVoiceView.as_view(), name='get_character_voice'),
    # 更新角色音色信息
    path('update/', UpdateCharacterVoiceView.as_view(), name='update_character_voice'),
]