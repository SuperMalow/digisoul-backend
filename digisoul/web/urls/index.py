from django.urls import path, include, re_path
from web.views.index import index

urlpatterns = [
    path('', index, name='index'),
    path('user/', include('web.urls.user')),
    path('token/', include('web.urls.token')),

    # 匹配所有非 media/、static/ 和 assets/ 的请求，并返回 index.html
    re_path(r'^(?!media/|static/|assets/).*$', index)
]