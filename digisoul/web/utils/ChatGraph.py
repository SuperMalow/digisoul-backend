from typing import Annotated
from langchain_openai import ChatOpenAI
import os
from typing import Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from langgraph.constants import START, END
from langgraph.graph import StateGraph

class ChatGraph:
    @staticmethod
    def create_char_app():
        llm = ChatOpenAI(
            model='qwen3.5-flash',
            base_url=os.getenv('API_BASE'),
            api_key=os.getenv('DASHSCOPE_API_KEY'),
        )

        class AgentState(TypedDict):
            # 等价于一个列表内 存在 message 列表，并且 message 列表可以被 add_messages 函数添加消息
            messages: Annotated[Sequence[BaseMessage], add_messages]

        def model_call(state: AgentState) -> AgentState:
            # 将state的消息传给大模型
            res = llm.invoke(state['messages'])
            # 再把大模型的返回结果添加到消息列表中
            return {'messages': [res]}

        # 最简单的模型，从 start -> agent -> end
        graph = StateGraph(AgentState)
        graph.add_node('agent', model_call)
        graph.add_edge(START, 'agent')
        graph.add_edge('agent', END)

        return graph.compile()
