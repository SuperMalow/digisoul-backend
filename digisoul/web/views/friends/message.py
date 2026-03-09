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
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, BaseMessageChunk
import json
from rest_framework.renderers import BaseRenderer
from django.http import StreamingHttpResponse
from web.serializers.friends.MessageSerializers import HistoryMessageSerializers

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
                input=json.dumps(
                    [m.model_dump()for m in inputs['messages']],
                    ensure_ascii=False,
                )[:10000],
                output=full_output[:10000],
                input_tokens=input_token,
                output_tokens=output_token,
                total_tokens=total_token,
            )

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Content-Type'] = 'text/event-stream'
        return response

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
