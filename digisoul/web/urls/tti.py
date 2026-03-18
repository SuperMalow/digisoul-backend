from django.urls import path
from web.views.tti.tti import (
    CharacterProfileOptimizationView,
    GenerateImagePromptView,
    GenerateImageView,
    GenerateImageTaskStatusView,
    GenerateImageTaskFileView,
)

urlpatterns = [
    # 角色性格优化
    path('tti/character/profile/optimization/', CharacterProfileOptimizationView.as_view(), name='character_profile_optimization'),
    # 根据角色性格生成图像
    path('tti/generate/image/prompt/', GenerateImagePromptView.as_view(), name='generate_image_prompt'),

    # 根据提示词生成图像
    path('tti/generate/image/', GenerateImageView.as_view(), name='generate_image'),
    # 根据 task_id 查询生成状态
    path('tti/generate/image/task/', GenerateImageTaskStatusView.as_view(), name='generate_image_task_status'),
    # 根据 task_id 获取生成图片文件（后端代理下载，规避浏览器跨域限制）
    path('tti/generate/image/task/file/', GenerateImageTaskFileView.as_view(), name='generate_image_task_file'),
]