from django.urls import path
from web.views.tti.tti import TTIView

urlpatterns = [
    path('tti/tti/', TTIView.as_view(), name='tti'),
]