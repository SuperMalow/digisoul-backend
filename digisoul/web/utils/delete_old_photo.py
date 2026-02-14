# 删除用户的旧头像辅助函数 
import os
from django.conf import settings

def delete_old_photo(photo):
    if photo and photo.name != 'user/photos/defaultUserPhoto.jpeg':
        old_path = os.path.join(settings.MEDIA_ROOT, photo.name)
        # 删除旧头像
        if os.path.exists(old_path):
            os.remove(old_path)
        