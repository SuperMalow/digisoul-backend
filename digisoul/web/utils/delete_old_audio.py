import os
from django.conf import settings

# 删除用户的旧语音文件辅助函数 
def delete_old_audio(audio):
    if audio:
        old_path = os.path.join(settings.MEDIA_ROOT, audio.name)
        # 删除旧语音文件
        if os.path.exists(old_path):
            os.remove(old_path)