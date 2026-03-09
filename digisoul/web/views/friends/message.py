# 角色与用户之间的聊天记录视图

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from web.models.Friends import Message, Friends
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from web.utils.ChatGraph import ChatGraph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, BaseMessageChunk
import json
from rest_framework.renderers import BaseRenderer
from django.http import StreamingHttpResponse

# 伪渲染器
class SSERenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'utf-8'
    charset = 'utf-8'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

# 获取角色与用户之间的聊天记录
class MessageChatView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [SSERenderer]
    def post(self, request):
        friend_uuid = request.data.get('friend_uuid')
        message = request.data.get('message')
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

        res = agent.invoke(inputs)
        # print(res['messages'])

        # 流式输出迭代器
        def event_stream():
            full_usage = {}
            for msg, metadata in agent.stream(inputs, stream_mode="messages"):
                if isinstance(msg, BaseMessageChunk):
                    if msg.content:
                        yield f'data: {json.dumps({'content': msg.content}, ensure_ascii=False)}\n\n'
                    if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                        full_usage = msg.usage_metadata
            yield 'data: [DONE]\n\n'
            
            print(full_usage)

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Content-Type'] = 'text/event-stream'
        return response

        
