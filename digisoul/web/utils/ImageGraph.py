from langchain_openai import ChatOpenAI
import os
from langgraph.graph import StateGraph
from langgraph.graph import MessagesState
from langgraph.constants import START, END
from langgraph.prebuilt import ToolNode
from langchain.tools import tool

@tool('generate_image', description='生成图片')
def generate_image(prompt: str) -> str:
    """根据提示词生成图片"""
    return '图片生成成功'

# 创建文字生成图片的图谱
class ImageGraph:

    @staticmethod
    def create_image_agent():
        tools = []
        llm = ChatOpenAI(
            model='qwen3-max',
            base_url=os.getenv('API_BASE'),
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            streaming=True,
            extra_body={"enable_thinking": False},
            model_kwargs={
                "stream_options": {
                    "include_usage": True, # 输出token的消耗数
                }
            }
        ).bind_tools(tools)

        def model_call(state: MessagesState) -> MessagesState:
            # 将 state 的消息传回给llm
            res = llm.invoke(state['messages'])
            return {'messages': [res]}

        def switch_tool(state: MessagesState) -> MessagesState:
            last_message = state['messages'][-1]
            if last_message.tool_calls:
                return "tools"
            return "end"

        toolsNode = ToolNode(tools)

        graph = StateGraph(MessagesState)
        graph.add_node('image', model_call)
        graph.add_node('tools', toolsNode)

        graph.add_edge(START, 'image')
        graph.add_conditional_edges(
            'image',
            switch_tool,
            {
                "tools": "tools",
                "end": END,
            },
        )
        graph.add_edge('tools', 'image')

        return graph.compile()