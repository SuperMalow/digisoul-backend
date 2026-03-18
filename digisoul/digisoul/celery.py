import os
from celery import Celery
from celery.signals import after_setup_logger
from datetime import timedelta
import logging
import requests

# 设置 django 的 settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digisoul.settings')

app = Celery('digisoul')

# 日志管理
@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    # 把日志发到控制台展示
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 配置 Celery
app.config_from_object('django.conf:settings', namespace='CELERY')
# 字段发现任务
app.autodiscover_tasks()

@app.task
def generate_image(text, negative_prompt):
    """根据 text 生成图片"""
    headers = {
        "Authorization": f"Bearer {os.getenv('DASHSCOPE_API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "qwen-image-2.0-pro",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": text
                        }
                    ]
                }
            ]
        },
        "parameters": {
            "negative_prompt": negative_prompt,
            "prompt_extend": True,
            "watermark": False,
            "size": "928*1664"
        }
    }   
    response = requests.post(os.getenv('IMAGE_URL'), headers=headers, json=data)
    return response.json()


@app.task
def create_voice(voice_url, prefix):
    """根据 voice_url 复刻音色"""
    headers = {
        "Authorization": f"Bearer {os.getenv('DASHSCOPE_API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "voice-enrollment",
        "input": {
            "action": "create_voice",
            "target_model": "cosyvoice-v3-flash",
            "prefix": prefix,
            "url": voice_url,
        }
    }
    response = requests.post(os.getenv('VOICE_URL'), headers=headers, json=data)
    return response.json()