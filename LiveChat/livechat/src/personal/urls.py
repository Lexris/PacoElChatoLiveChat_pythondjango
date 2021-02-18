from django.urls import path
from personal.views import room, lobby_select

app_name = 'personal'

urlpatterns = [
    path('', lobby_select, name='lobby-select'),
    path('<str:room_name>/', room, name='room'),
]