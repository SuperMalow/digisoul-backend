import asyncio
import base64
import json
import os
import queue
import threading
import uuid

import websockets

SENTENCE_ENDS = frozenset('。！？；\n')
SENTENCE_END_MARKER = '__SENTENCE_END__'


def split_sentences(buffer):
    """
    在 buffer 中找到最后一个句子边界，返回 (要发送的句子, 剩余缓冲).
    如果没有找到句子边界，返回 (None, 原始buffer).
    """
    last_boundary = -1
    for i, char in enumerate(buffer):
        if char in SENTENCE_ENDS:
            last_boundary = i
    if last_boundary >= 0:
        return buffer[:last_boundary + 1], buffer[last_boundary + 1:]
    return None, buffer


def _get_run_task_header(task_id):
    return json.dumps({
        "header": {
            "action": "run-task",
            "task_id": task_id,
            "streaming": "duplex"
        },
        "payload": {
            "task_group": "audio",
            "task": "tts",
            "function": "SpeechSynthesizer",
            "model": "cosyvoice-v3-flash",
            "parameters": {
                "text_type": "PlainText",
                "voice": "longfeifei_v3",
                "format": "mp3",
                "sample_rate": 22050, # 采样率
                "volume": 52, # 音量
                "rate": 1.2, # 语速
                "pitch": 1.09 # 音调
            },
            "input": {}
        }
    })


def _get_continue_task_header(task_id, text):
    return json.dumps({
        "header": {
            "action": "continue-task",
            "task_id": task_id,
            "streaming": "duplex"
        },
        "payload": {
            "input": {"text": text}
        }
    }, ensure_ascii=False)


def _get_finish_task_header(task_id):
    return json.dumps({
        "header": {
            "action": "finish-task",
            "task_id": task_id,
            "streaming": "duplex"
        },
        "payload": {
            "input": {}
        }
    })


async def _tts_sender(text_q, ws, task_id, llm_done_event):
    """从队列中读取句子并发送到 TTS WebSocket."""
    loop = asyncio.get_event_loop()
    while True:
        try:
            # 从队列中读取句子并发送到 TTS WebSocket
            text = await loop.run_in_executor(
                None, lambda: text_q.get(timeout=0.15)
            )
        except queue.Empty:
            if llm_done_event.is_set() and text_q.empty():
                break
            continue

        print(f"[TTSHelper] sending text: {text[:50]}")
        await ws.send(_get_continue_task_header(task_id, text))

    print("[TTSHelper] sending finish-task")
    await ws.send(_get_finish_task_header(task_id))


async def _tts_receiver(ws, audio_q):
    """从 TTS WebSocket 接收音频数据并放入队列."""
    chunk_count = 0
    async for msg in ws:
        if isinstance(msg, bytes):
            audio_b64 = base64.b64encode(msg).decode('utf-8')
            audio_q.put(audio_b64)
            chunk_count += 1
        else:
            data = json.loads(msg)
            event = data['header']['event']
            if event == 'task-failed':
                err_code = data['header'].get('error_code', '')
                err_msg = data['header'].get('error_message', '')
                print(f"[TTSHelper] task-failed: {err_code} - {err_msg}")
                break
            if event == 'task-finished':
                print(f"[TTSHelper] task-finished, audio_chunks={chunk_count}")
                break
            if event == 'result-generated':
                output_type = data.get('payload', {}).get('output', {}).get('type', '')
                if output_type == 'sentence-end':
                    audio_q.put(SENTENCE_END_MARKER)


async def run_tts_pipeline(text_q, audio_q, llm_done_event):
    """管理完整的 TTS WebSocket 会话：从 text_q 读取文字，将音频放入 audio_q."""
    task_id = uuid.uuid4().hex
    api_key = os.getenv('DASHSCOPE_API_KEY')
    wss_url = os.getenv('WSS_URL')
    headers = {'Authorization': f'Bearer {api_key}'}

    print(f"[TTSHelper] connecting, task_id={task_id}")
    async with websockets.connect(wss_url, additional_headers=headers) as ws:
        await ws.send(_get_run_task_header(task_id))

        # 监听是否返回task-started事件，开始握手
        async for msg in ws:
            data = json.loads(msg)
            if data['header']['event'] == 'task-started':
                print("[TTSHelper] task-started received")
                break

        # 跟TTS模型握手成功，开始建立发送和接收的异步任务
        await asyncio.gather(
            _tts_sender(text_q, ws, task_id, llm_done_event),
            _tts_receiver(ws, audio_q),
        )


def start_tts_thread(text_q, audio_q, llm_done_event):
    """启动一个守护线程运行 TTS 管道. 返回 (thread, tts_done_event)."""
    tts_done_event = threading.Event()

    def worker():
        try:
            asyncio.run(run_tts_pipeline(text_q, audio_q, llm_done_event))
        except Exception as e:
            print(f"[TTSHelper] pipeline error: {e}")
        finally:
            tts_done_event.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread, tts_done_event
