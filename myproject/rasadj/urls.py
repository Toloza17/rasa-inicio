from django.urls import path
from . import views

urlpatterns = [
    path('consultas/', views.respuestas, name='consultas'),
    path('action/', views.rasa_chat, name='rasa_chat'),  # Nueva ruta para interactuar con Rasa
]
