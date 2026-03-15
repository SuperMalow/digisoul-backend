# 角色与用户之间的聊天记录视图

import base64
import json
import queue
import threading

from telnetlib import EC
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.renderers import BaseRenderer
from django.http import StreamingHttpResponse
from django.core.files.base import ContentFile
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, BaseMessageChunk, SystemMessage

from web.models.Friends import Message, Friends
from web.models.Prompt import SystemPrompt
from web.utils.ChatGraph import ChatGraph
from web.utils.MemoryGraph import update_memory
from web.utils.TTSHelper import split_sentences, start_tts_thread, SENTENCE_END_MARKER
from web.serializers.friends.MessageSerializers import HistoryMessageSerializers

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

        enable_tts = str(request.data.get('enable_tts', '')).lower() in ('true', '1')

        if enable_tts:
            stream_iter = self.event_stream_with_tts(agent, inputs, friend, message, audio_message)
        else:
            stream_iter = self.event_stream(agent, inputs, friend, message, audio_message)

        response = StreamingHttpResponse(stream_iter, content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Content-Type'] = 'text/event-stream'
        response['X-Accel-Buffering'] = 'no'
        return response

    def _save_message(self, friend, message, audio_message, inputs, full_output, full_usage, tts_audio_file=None):
        input_token = full_usage.get('input_tokens', 0)
        output_token = full_usage.get('output_tokens', 0)
        total_token = full_usage.get('total_tokens', 0)
        Message.objects.create(
            friend=friend,
            user_message=message[:5000],
            audio_message=audio_message if audio_message else None,
            tts_audio=tts_audio_file,
            input=json.dumps(
                [m.model_dump() for m in inputs['messages']],
                ensure_ascii=False,
            )[:10000],
            output=full_output[:10000],
            input_tokens=input_token,
            output_tokens=output_token,
            total_tokens=total_token,
        )
        if Message.objects.filter(friend=friend).count() % 10 == 0:
            update_memory(friend)

    # 纯文字流式输出
    def event_stream(self, agent, inputs, friend, message, audio_message):
        full_output = ''
        full_usage = {}
        for msg, metadata in agent.stream(inputs, stream_mode="messages"):
            if isinstance(msg, BaseMessageChunk):
                if msg.content:
                    full_output += msg.content
                    yield f'data: {json.dumps({"content": msg.content}, ensure_ascii=False)}\n\n'
                if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    full_usage = msg.usage_metadata
        yield 'data: [DONE]\n\n'
        self._save_message(friend, message, audio_message, inputs, full_output, full_usage)

    @staticmethod
    def _yield_audio_events(audio_q, collector=None, blocking=False, timeout=0.1):
        """从 audio_q 中取出数据并生成 SSE 事件, 遇到 SENTENCE_END_MARKER 生成 audio_end.
        如果传入 collector (list), 同时将 base64 音频块追加进去用于后续保存."""
        while True:
            try:
                item = audio_q.get(timeout=timeout) if blocking else audio_q.get_nowait()
            except queue.Empty:
                break
            if item == SENTENCE_END_MARKER:
                yield f'data: {json.dumps({"audio_end": True})}\n\n'
            else:
                if collector is not None:
                    collector.append(item)
                yield f'data: {json.dumps({"audio": item}, ensure_ascii=False)}\n\n'

    # 文字 + TTS 音频并行流式输出
    def event_stream_with_tts(self, agent, inputs, friend, message, audio_message):
        full_output = ''
        full_usage = {}
        sentence_buffer = ''
        audio_b64_chunks = []

        text_q = queue.Queue()
        audio_q = queue.Queue()
        llm_done_event = threading.Event()

        _, tts_done_event = start_tts_thread(text_q, audio_q, llm_done_event)

        for msg, metadata in agent.stream(inputs, stream_mode="messages"):
            if isinstance(msg, BaseMessageChunk):
                if msg.content:
                    full_output += msg.content
                    yield f'data: {json.dumps({"content": msg.content}, ensure_ascii=False)}\n\n'

                    sentence_buffer += msg.content
                    sentence, sentence_buffer = split_sentences(sentence_buffer)
                    if sentence and sentence.strip():
                        text_q.put(sentence)

                if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    full_usage = msg.usage_metadata

            yield from self._yield_audio_events(audio_q, collector=audio_b64_chunks)

        if sentence_buffer.strip():
            text_q.put(sentence_buffer)

        llm_done_event.set()

        while not tts_done_event.is_set() or not audio_q.empty():
            yield from self._yield_audio_events(audio_q, collector=audio_b64_chunks, blocking=True)

        yield 'data: [DONE]\n\n'

        tts_file = None
        if audio_b64_chunks:
            audio_bytes = b''.join(base64.b64decode(chunk) for chunk in audio_b64_chunks)
            tts_file = ContentFile(audio_bytes, name='tts_response.mp3')

        self._save_message(friend, message, audio_message, inputs, full_output, full_usage, tts_file)

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
