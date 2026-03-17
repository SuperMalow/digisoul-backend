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

from web.models.Prompt import SystemPrompt

# 文字生成图片
class TTIView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request):
        character_uuid = request.data.get('character_uuid')

        if not character_uuid:
            return Response({'result': 'error', 'message': '没有权限操作', 'errors': 'character_uuid is null'}, status=status.HTTP_401_UNAUTHORIZED)
        
        character = Character.objects.filter(uuid=character_uuid, author=request.user).first()
        if not character:
            return Response({'result': 'error', 'message': '角色不存在', 'errors': 'character not found'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 创建文字生成图片的图谱
        agent = ImageGraph.create_image_agent()

        message = character.profile

        # 创建输入
        inputs = {
            'messages': [HumanMessage(content=message)]
        }

        # 添加系统和用户提示词
        inputs = self._add_system_prompt(inputs, character)
        inputs = self._add_user_prompt(inputs, character)

        # 执行图谱
        res = agent.invoke(inputs)
        print('res => ', res)
        return Response({'result': 'success', 'message': '图片生成成功', 'data': res}, status=status.HTTP_200_OK)
    
    def _add_system_prompt(self, state, character):
        msgs = state['messages']
        system_prompt = SystemPrompt.objects.filter(title='图像格式').order_by('order_number')
        prompt = ''
        for p in system_prompt:
            prompt += p.prompt
        return {'messages': [SystemMessage(content=prompt)] + msgs}

    def _add_user_prompt(self, state, character):
        msgs = state['messages']
        message = character.profile
        prompt = f'\n[用户想要创建的角色介绍]: {message}\n'
        return {'messages': [HumanMessage(content=prompt)] + msgs}