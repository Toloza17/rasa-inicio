from django.urls import path
from . import views

urlpatterns = [
    path('menu/', views.menu, name='menu'),
    path('action/', views.rasa_chat, name='rasa_chat'),
    path('respuestas/', views.respuestas, name='respuestas'),  # asegúrate de que esta ruta coincide con la del HTML
]