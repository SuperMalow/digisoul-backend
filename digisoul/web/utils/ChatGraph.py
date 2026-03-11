from typing import Annotated
from langchain_openai import ChatOpenAI
import os
from typing import Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langchain.tools import tool
from django.utils.timezone import localtime, now
from langgraph.prebuilt import ToolNode

# 工具函数
@tool
def get_datetime():
    """查询当前的时间，返回格式为：年-月-日 时:分:秒"""
    return localtime(now()).strftime('%Y-%m-%d %H:%M:%S')

# 创建角色对话图谱
class ChatGraph:
    @staticmethod
    def create_char_app(thinking_enabled=False):
        tools = [get_datetime]
        llm = ChatOpenAI(
            model='qwen3.5-flash',
            base_url=os.getenv('API_BASE'),
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            streaming=True,
            extra_body={"enable_thinking": thinking_enabled},
            model_kwargs={
                "stream_options": {
                    "include_usage": True, # 蔬菜token的消耗数
                }
            },
        ).bind_tools(tools)

        class AgentState(TypedDict):
            # 等价于一个列表内 存在 message 列表，并且 message 列表可以被 add_messages 函数添加消息
            messages: Annotated[Sequence[BaseMessage], add_messages]

        def model_call(state: AgentState) -> AgentState:
            # 将state的消息传给大模型
            res = llm.invoke(state['messages'])
            # 再把大模型的返回结果添加到消息列表中
            return {'messages': [res]}

        def switch_tool(state: AgentState) -> AgentState:
            last_message = state['messages'][-1]
            if last_message.tool_calls:
                return "tools"
            return "end"

        toolsNode = ToolNode(tools)

        # 最简单的模型，从 start -> agent -> end
        graph = StateGraph(AgentState)
        graph.add_node('agent', model_call)
        graph.add_node('tools', toolsNode)

        graph.add_edge(START, 'agent')
         # 通过 switch_tool 函数返回的信息，决定下一步的节点s
        graph.add_conditional_edges(
            'agent',
            switch_tool,
            {
                "tools": "tools",
                "end": END,
            },
        )
        graph.add_edge('tools', 'agent')

        return graph.compile()
