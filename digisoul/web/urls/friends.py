from django.urls import path

from web.views.friends.friends import CreateFriendsView, DeleteFriendsView, GetFriendsListView
from web.views.friends.message import MessageChatView

urlpatterns = [
    path('create/', CreateFriendsView.as_view(), name='create_friends'),
    path('delete/', DeleteFriendsView.as_view(), name='delete_friends'),
    path('list/', GetFriendsListView.as_view(), name='get_friends_list'),

    # message
    path('message/chat/', MessageChatView.as_view(), name='message_chat'),
]