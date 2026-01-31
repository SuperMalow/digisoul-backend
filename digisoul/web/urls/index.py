from django.urls import path, include

from web.views.index import index

urlpatterns = [
    path('', index, name='index'),
    path('user/', include('web.urls.user')),
    path('token/', include('web.urls.token')),
]