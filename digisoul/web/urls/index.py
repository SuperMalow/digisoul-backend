from django.urls import path, include, re_path
from web.views.index import index

urlpatterns = [
    # path('', index, name='index'),
    path('api/user/', include('web.urls.user')),
    path('api/token/', include('web.urls.token')),
    path('api/character/', include('web.urls.character')),
    path('api/friends/', include('web.urls.friends')),
    path('api/character/settings/', include('web.urls.characterSettings')),
    path('api/character/voice/', include('web.urls.characterVoice')),
    path('api/tti/', include('web.urls.tti')),

    # # 匹配所有非 media/、static/ 和 assets/ 的请求，并返回 index.html
    # re_path(r'^(?!media/|static/|assets/).*$', index)
]