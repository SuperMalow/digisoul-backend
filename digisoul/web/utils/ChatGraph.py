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
import lancedb
from langchain_community.vectorstores import LanceDB
from web.documents.utils.custom_embeddings import CustomEmbeddings
from pprint import pprint

@tool('get_datetime', description='在用户想要查询当前日期时间，优先使用该工具')
def get_datetime():
    """查询当前的时间，返回格式为：年-月-日 时:分:秒"""
    return localtime(now()).strftime('%Y-%m-%d %H:%M:%S')

@tool('search_knowledge_base', description='在用户想要查询阿里云百炼平台的相关信息，优先使用该工具')
def search_knowledge_base(question: str):
    """当用户查询阿里云百炼平台相关信息时，使用该工具。输入为用户的问题，输出为查询的结果。"""
    db = lancedb.connect('web/documents/db/lancedb_storage')
    embeddings = CustomEmbeddings()
    vector_db = LanceDB(
        embedding=embeddings,
        connection=db,
        table_name='my_knowledge_base',
    )
    docs = vector_db.similarity_search(question, k=3)
    context = '\n\n'.join([f'内容片段：{i + 1}\n{doc.page_content}' for i, doc in enumerate(docs)])
    return f'从数据内查找到以下相关信息：\n\n{context}\n'


# 创建角色对话图谱
class ChatGraph:
    @staticmethod
    def create_char_app(thinking_enabled=False):
        tools = [get_datetime, search_knowledge_base]
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
            # pprint(state['messages'])
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
