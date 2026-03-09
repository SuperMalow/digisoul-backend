# 角色与用户之间的聊天记录视图

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from web.models.Friends import Message, Friends
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from web.utils.ChatGraph import ChatGraph
from langchain_core.messages import HumanMessage, AIMessage

# 获取角色与用户之间的聊天记录
class MessageChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_uuid = request.data.get('friend_uuid')
        message = request.data.get('message').strip()
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
        print(res['messages'])

        return Response({'result': 'success', 'message': '消息发送成功', 'data': res['messages'][-1].content}, status=status.HTTP_200_OK)
