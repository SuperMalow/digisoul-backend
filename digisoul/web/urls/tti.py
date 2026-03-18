from django.urls import path
from web.views.tti.tti import CharacterProfileOptimizationView, TTIView

urlpatterns = [
    # 角色性格优化
    path('tti/character/profile/optimization/', CharacterProfileOptimizationView.as_view(), name='character_profile_optimization'),
    # 根据角色性格生成图像
    path('tti/tti/', TTIView.as_view(), name='tti'),
]