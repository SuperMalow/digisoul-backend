from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import asyncio
import uuid
import os
import websockets
import json

# 语音识别视图
class ASRView(APIView):
    permission_classes=[IsAuthenticated]

    def _get_run_task_header(self, task_id):
        """
        返回包装好的任务开始的header
        """
        header = json.dumps({
            	"header": {
                "streaming": "duplex",
                "task_id": task_id,
                "action": "run-task"
            },
            "payload": {
                "model": "gummy-realtime-v1",
                "parameters": {
                    "sample_rate": 16000,
                    "format": "pcm",
                    "transcription_enabled": True,
                },
                "input": {},
                "task": "asr",
                "task_group": "audio",
                "function": "recognition"
            }
        })
        return header

    def _get_task_finished_header(self, task_id):
        header = json.dumps({
            "header": {
                "task_id": task_id,
                "event": "task-finished",
                "attributes": {}
            },
            "payload": {
                "output": {},
            }
        })
        return header

    async def asr_sender(self, pcm_data, ws, task_id):
        chunk = 3200
        # print("开始发送语音信息!")
        for i in range(0, len(pcm_data), chunk):
            await ws.send(pcm_data[i: i+chunk])
            await asyncio.sleep(0.1)
        # print("发送语音信息完毕!")
        # 发送完毕后，发送结束事件
        finished_header = self._get_task_finished_header(task_id)
        await ws.send(finished_header)

    async def asr_receiver(self, ws):
        text = ''
        # print("开始接受语音信息!")
        async for msg in ws:
            data = json.loads(msg)
            event = data['header']['event'] 
            if event == 'result-generated':
                output = data['payload']['output']
                if output.get('transcription', None) and output.get('transcription').get('sentence_end', None):
                    text += output['transcription']['text']
            elif event == 'task-finished' or event == 'task-failed':
                break
        print("接受语音信息完毕!")
        return text

    async def run_asr_task(self, pcm_data):
        task_id = uuid.uuid4().hex
        api_key = os.getenv('DASHSCOPE_API_KEY')
        wss_url = os.getenv('WSS_URL')
        headers = {
            'Authorization': f'Bearer {api_key}',
        }
        async with websockets.connect(wss_url, additional_headers=headers) as ws:
            await ws.send(self._get_run_task_header(task_id))

            # 监听是否返回task_started事件
            async for msg in ws:
                if json.loads(msg)['header']['event'] == 'task-started':
                    break
            
            # 握手成功，开始发送和接受消息
            sender_result, receiver_result = await asyncio.gather(
                self.asr_sender(pcm_data, ws, task_id),
                self.asr_receiver(ws),
            )
            return receiver_result

    def post(self, request):
        audio = request.FILES.get('audio')
        print("audio ==> ", audio)
        if not audio:
            return Response({'result': 'error', 'message': '音频不存在', 'erros': 'audio不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        pcm_data = audio.read()
        print("pcm_data ==> ", len(pcm_data))
        text = asyncio.run(self.run_asr_task(pcm_data))
        return Response({'result': 'success', 'message': '音频识别成功', 'text': text}, status=status.HTTP_200_OK)