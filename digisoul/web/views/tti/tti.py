from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import asyncio
import uuid
import os
import websockets
import json
from pprint import pprint
from web.models.Character import Character
from web.utils.ImageGraph import ImageGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages import BaseMessageChunk
from django.http import StreamingHttpResponse
from rest_framework.renderers import BaseRenderer
from web.models.Prompt import SystemPrompt
from digisoul.celery import generate_image
from digisoul.celery import app as celery_app
from celery.result import AsyncResult
from django.http import HttpResponse
import requests


# 伪类渲染器
class SSERenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'utf-8'
    charset = 'utf-8'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

# 流式输出
def event_stream(agent, inputs):
    full_output = ''
    for msg, metadata in agent.stream(inputs, stream_mode="messages"):
        print('msg => ', msg)
        if isinstance(msg, BaseMessageChunk):
            if msg.content:
                full_output += msg.content
                yield f'data: {json.dumps({
                    "content": msg.content
                }, ensure_ascii=False)}\n\n'
    yield 'data: [DONE]\n\n'


def extract_image_url(payload):
    if not isinstance(payload, dict):
        return ''
    # 兼容多种返回结构：
    # 1) output.results[0].url
    # 2) output.choices[0].message.content[0].image
    # 3) output.url / payload.url
    output = payload.get('output')
    if isinstance(output, dict):
        results = output.get('results')
        if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict):
            url = results[0].get('url')
            if url:
                return url
        choices = output.get('choices')
        if isinstance(choices, list) and len(choices) > 0 and isinstance(choices[0], dict):
            message = choices[0].get('message')
            if isinstance(message, dict):
                content = message.get('content')
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('image'):
                            return item.get('image')
        if output.get('url'):
            return output.get('url')
    if payload.get('url'):
        return payload.get('url')
    return ''

# 角色性格优化
class CharacterProfileOptimizationView(APIView):
    permission_classes=[IsAuthenticated]
    renderer_classes = [SSERenderer]

    # 添加性格优化系统提示词
    def _add_system_prompt(self, state, character):
        msgs = state['messages']
        system_prompt = SystemPrompt.objects.filter(title='性格优化').order_by('order_number')
        prompt = ''
        print('查询到 性格优化 系统提示词 ===> ', len(system_prompt))
        for p in system_prompt:
            prompt += p.prompt
        prompt += f'\n[角色名字]: {character.name}\n'
        prompt += f'\n[角色性别]: {character.gender}\n'
        prompt += f'\n[用户原本所描述的角色介绍]: {character.profile}\n\n'
        return {'messages': [SystemMessage(content=prompt)] + msgs}

    # 性格优化请求
    def post(self, request):
        character_uuid = request.data.get('character_uuid')
        character_description = request.data.get('character_description')
        if not character_uuid:
            return Response({'result': 'error', 'message': '没有权限操作', 'errors': 'character_uuid is null'}, status=status.HTTP_401_UNAUTHORIZED)
        if not character_description:
            return Response({'result': 'error', 'message': 'character_description不能为空', 'errors': 'character_description is null'}, status=status.HTTP_401_UNAUTHORIZED)
        character = Character.objects.filter(uuid=character_uuid, author=request.user).first()
        if not character:
            return Response({'result': 'error', 'message': '角色不存在', 'errors': 'character not found'}, status=status.HTTP_401_UNAUTHORIZED)

        # 调用大模型
        agent = ImageGraph.create_image_agent()
        # 创建输入
        new_description = f'[当前用户描述的角色介绍]: {character_description}\n'
        inputs = {
            'messages': [HumanMessage(content=new_description)]
        }
        inputs = self._add_system_prompt(inputs, character)

        response = StreamingHttpResponse(event_stream(agent, inputs), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Content-Type'] = 'text/event-stream'
        response['X-Accel-Buffering'] = 'no'
        return response

# 根据角色性格生成文生图提示词
class GenerateImagePromptView(APIView):
    permission_classes=[IsAuthenticated]
    renderer_classes = [SSERenderer]

    def post(self, request):
        character_uuid = request.data.get('character_uuid')
        if not character_uuid:
            return Response({'result': 'error', 'message': '角色不存在', 'errors': 'character_uuid is null'}, status=status.HTTP_401_UNAUTHORIZED)
        
        character = Character.objects.filter(uuid=character_uuid, author=request.user).first()
        if not character:
            return Response({'result': 'error', 'message': '没有权限操作', 'errors': 'character not found'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 创建文字生成图片的图谱
        agent = ImageGraph.create_image_agent()

        message = ''
        message += f'\n[角色名字]: {character.name}\n'
        message += f'\n[角色性别]: {character.gender}\n'
        message += f'\n[用户想要创建的角色介绍]: {character.profile}\n'

        # 创建输入
        inputs = {
            'messages': [HumanMessage(content=message)]
        }

        # 添加系统和用户提示词
        inputs = self._add_system_prompt(inputs)

        # 执行图谱 - 流式输出
        response = StreamingHttpResponse(event_stream(agent, inputs), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Content-Type'] = 'text/event-stream'
        response['X-Accel-Buffering'] = 'no'
        return response
    
    def _add_system_prompt(self, state):
        msgs = state['messages']
        system_prompt = SystemPrompt.objects.filter(title='生图提示词').order_by('order_number')
        prompt = ''
        print('查询到 生图提示词 系统提示词 ===> ', len(system_prompt))
        for p in system_prompt:
            prompt += p.prompt
        return {'messages': [SystemMessage(content=prompt)] + msgs}

# 根据提示词生成图像
class GenerateImageView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request):
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({'result': 'error', 'message': '提示词不能为空', 'errors': 'prompt is null'}, status=status.HTTP_401_UNAUTHORIZED)
        negative_prompt = 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, generic, out of focus, distorted, horror, disfigured, missing limbs'
        # 通过 celery 异步执行生成图像任务
        task = generate_image.delay(prompt, negative_prompt)

        return Response({
            'result': 'success',
            'message': '生成图像任务已提交',
            'task_id': task.id
        }, status=status.HTTP_200_OK)


class GenerateImageTaskStatusView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'result': 'error', 'message': 'task_id不能为空', 'errors': 'task_id is null'}, status=status.HTTP_400_BAD_REQUEST)

        task = AsyncResult(task_id, app=celery_app)

        if task.state in ('PENDING', 'RECEIVED', 'STARTED', 'RETRY'):
            return Response({
                'result': 'success',
                'message': '任务处理中',
                'status': task.state,
                'task_id': task_id
            }, status=status.HTTP_200_OK)

        if task.state == 'FAILURE':
            return Response({
                'result': 'error',
                'message': '任务执行失败',
                'status': task.state,
                'task_id': task_id,
                'errors': str(task.info) if task.info else '生成图片失败'
            }, status=status.HTTP_200_OK)

        result = task.result if isinstance(task.result, dict) else {}
        image_url = extract_image_url(result)
        return Response({
            'result': 'success',
            'message': '任务执行成功',
            'status': task.state,
            'task_id': task_id,
            'image_url': image_url,
            'data': result
        }, status=status.HTTP_200_OK)


class GenerateImageTaskFileView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'result': 'error', 'message': 'task_id不能为空', 'errors': 'task_id is null'}, status=status.HTTP_400_BAD_REQUEST)

        task = AsyncResult(task_id, app=celery_app)
        if task.state != 'SUCCESS':
            return Response({
                'result': 'error',
                'message': '任务未完成，无法获取图片',
                'status': task.state,
                'task_id': task_id,
                'errors': 'task is not success'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = task.result if isinstance(task.result, dict) else {}
        image_url = extract_image_url(result)
        if not image_url:
            return Response({'result': 'error', 'message': '未找到图片地址', 'errors': 'image_url is null'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image_response = requests.get(image_url, timeout=20)
        except Exception as err:
            return Response({'result': 'error', 'message': '下载图片失败', 'errors': str(err)}, status=status.HTTP_502_BAD_GATEWAY)

        if image_response.status_code != 200:
            return Response({'result': 'error', 'message': '下载图片失败', 'errors': f'status_code={image_response.status_code}'}, status=status.HTTP_502_BAD_GATEWAY)

        content_type = image_response.headers.get('Content-Type', 'image/png')
        response = HttpResponse(image_response.content, content_type=content_type)
        response['Cache-Control'] = 'no-store'
        return response