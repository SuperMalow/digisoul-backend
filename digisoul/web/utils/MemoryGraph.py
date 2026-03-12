import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from typing import Annotated, Sequence
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from web.models.Prompt import SystemPrompt
from web.models.Friends import Message
from django.utils.timezone import now
from pprint import pprint

# 长期记忆处理图谱
class MemoryGraph:
    @staticmethod
    def create_memory_app():
        llm = ChatOpenAI(
            model='qwen3.5-flash',
            base_url=os.getenv('API_BASE'),
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            extra_body={"enable_thinking": False},
        )

        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]

        def model_call(state: AgentState) -> AgentState:
            res = llm.invoke(state['messages'])
            return {'messages': [res]}

        graph = StateGraph(AgentState)
        graph.add_node('memory', model_call)

        graph.add_edge(START, 'memory')
        graph.add_edge('memory', END)

        return graph.compile()

# 将系统提示词添加到对话当中
def create_system_prompt():
    system_prompts = SystemPrompt.objects.filter(title='记忆').order_by('order_number')
    prompt = ''
    for sp in system_prompts:
        prompt += sp.prompt
    return SystemMessage(content=prompt)


# 将好友信息添加到对话当中
def create_human_message(friend):
    prompt = f'[原始记忆]\n{friend.memory}\n'
    prompt += f'[最近对话]\n'
    messages = list(Message.objects.filter(friend=friend).order_by('-created_at')[:10])
    messages.reverse()
    for message in messages:
        prompt += f'user: {message.user_message}\n'
        prompt += f'assistant: {message.output}\n'
    return HumanMessage(content=prompt)
    

# 更新长期记忆到数据库当中
def update_memory(friend):
    app = MemoryGraph.create_memory_app()

    inputs = {
        'messages': [
            create_system_prompt(),
            create_human_message(friend),
        ]
    }

    # pprint(inputs)
    res = app.invoke(inputs)
    friend.memory = res['messages'][-1].content
    pprint(friend.memory)
    friend.updated_at = now()
    friend.save()
