from django.urls import path
from web.views.character.character import UpdateCharacterView, CreateCharacterView, DeleteCharacterView, GetCharacterView, GetCharacterListView

urlpatterns = [
    path('update/', UpdateCharacterView.as_view(), name='update_character'),
    path('create/', CreateCharacterView.as_view(), name='create_character'),
    path('delete/', DeleteCharacterView.as_view(), name='delete_character'),
    path('get/', GetCharacterView.as_view(), name='get_character'),
    path('list/', GetCharacterListView.as_view(), name='list_character'),
]