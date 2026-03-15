# 角色与用户之间的聊天记录视图

from telnetlib import EC
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from web.models.Friends import Message, Friends
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from web.utils.ChatGraph import ChatGraph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, BaseMessageChunk, SystemMessage
import json
from rest_framework.renderers import BaseRenderer
from django.http import StreamingHttpResponse
from web.serializers.friends.MessageSerializers import HistoryMessageSerializers
from web.models.Prompt import SystemPrompt
from web.utils.MemoryGraph import update_memory

# 伪渲染器
class SSERenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'utf-8'
    charset = 'utf-8'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

# 手动添加系统提示词
def add_system_prompt(state, friends):
    msgs = state['messages']
    system_prompt = SystemPrompt.objects.filter(title='角色与用户之间的聊天记录').order_by('order_number')
    prompt = ''
    for prompt  in system_prompt:
        prompt += prompt.prompt
    prompt += f'\n[角色性格]: {friends.character.profile}\n'
    # 添加长期记忆
    prompt += f'\n[长期记忆]: {friends.memory}\n'
    return {'messages': [SystemMessage(content=prompt)] + msgs}

# 手动添加最近的十条对话内容
def add_recent_messages(state, friends):
    msgs = state['messages']
    messages = list(Message.objects.filter(friend=friends).order_by('-created_at')[:10])
    messages.reverse()
    fianl_messages = []
    for message in messages:
        fianl_messages.append(HumanMessage(content=message.user_message))
        fianl_messages.append(AIMessage(content=message.output))
    return {'messages': msgs[:1] + fianl_messages + msgs[-1:]}

# 获取角色与用户之间的聊天记录
class MessageChatView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [SSERenderer]
    def post(self, request):
        friend_uuid = request.data.get('friend_uuid')
        message = request.data.get('message')
        audio_message = request.FILES.get('audio_files')

        if not message:
            return Response({'result': 'error', 'message': 'message不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if not friend_uuid:
            return Response({'result': 'error', 'message': 'friend_uuid不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        friends = Friends.objects.filter(uuid=friend_uuid, me=request.user)
        if not friends.exists():
            return Response({'result': 'error', 'message': '好友不存在'}, status=status.HTTP_404_NOT_FOUND)
        friend = friends.first()
        agent = ChatGraph.create_char_app()

        inputs = {
            'messages': [HumanMessage(content=message)]
        }

        # 添加系统提示词语
        inputs = add_system_prompt(inputs, friend)
        inputs = add_recent_messages(inputs, friend)

        # 流式输出响应
        response = StreamingHttpResponse(
            self.event_stream(agent, inputs, friend, message, audio_message),
            content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Content-Type'] = 'text/event-stream'
        response['X-Accel-Buffering'] = 'no' # 防止nginx缓存，起不到很好的流式效果
        return response

    # 流式输出迭代器
    def event_stream(self, agent, inputs, friend, message, audio_message):
        full_output = ''
        full_usage = {}
        for msg, metadata in agent.stream(inputs, stream_mode="messages"):
            if isinstance(msg, BaseMessageChunk):
                if msg.content:
                    full_output += msg.content
                    yield f'data: {json.dumps({'content': msg.content}, ensure_ascii=False)}\n\n'
                if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    full_usage = msg.usage_metadata
        yield 'data: [DONE]\n\n'
        
        input_token = full_usage.get('input_tokens', 0)
        output_token = full_usage.get('output_tokens', 0)
        total_token = full_usage.get('total_tokens', 0)
        Message.objects.create(
            friend=friend,
            user_message=message[:5000],
            audio_message=audio_message if audio_message else None,
            input=json.dumps(
                [m.model_dump()for m in inputs['messages']],
                ensure_ascii=False,
            )[:10000],
            output=full_output[:10000],
            input_tokens=input_token,
            output_tokens=output_token,
            total_tokens=total_token,
        )
        # 每10条消息更新一次长期记忆
        if Message.objects.filter(friend=friend).count() % 10 == 0:
            update_memory(friend)

# 获取历史消息分页器
class MessageHistoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20
        
# 获取历史消息
class GetMessageHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HistoryMessageSerializers
    pagination_class = MessageHistoryPagination

    def get_queryset(self):
        friend_uuid = self.request.query_params.get('friend_uuid')
        if not friend_uuid:
            return Response({'result': 'error', 'message': 'friend_uuid不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        return Message.objects.filter(friend__uuid=friend_uuid, friend__me=self.request.user).order_by('-created_at')
