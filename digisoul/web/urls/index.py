from django.urls import path

from web.views.index import index

urlpatterns = [
    path('', index, name='index'),
]