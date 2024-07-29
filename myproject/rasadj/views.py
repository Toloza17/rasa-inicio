from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import pregunta, palabrabaneada
import json
import re
import random
import unicodedata
import requests

def normalizar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto.strip()

def validar_pregunta(user_question):
    keywords = ["problema", "ayuda", "soporte", "ayúdame", "error", "tengo un error", 'duda', 'estoy experimentando un error','otro']
    for keyword in keywords:
        if keyword in user_question.lower():
            return keyword, True
    return None, False

def contiene_palabra_baneada(texto):
    palabras_baneadas = palabrabaneada.objects.values_list('palabra', flat=True)
    for palabra in palabras_baneadas:
        if palabra in texto:
            return True
    return False

@csrf_exempt
def rasa_chat(request):
    if request.method == 'POST':
        # Manejo de datos en formato JSON
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_question = data.get('question')
                sub_question = data.get('sub_question', '')  # Obtén la opción secundaria si está disponible
                if not user_question:
                    return JsonResponse({"error": "Pregunta no proporcionada"}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Cuerpo de solicitud inválido"}, status=400)
        else:
            # Manejo de datos enviados desde un formulario
            user_question = request.POST.get('question')
            sub_question = request.POST.get('sub_question', '')  # Obtén la opción secundaria si está disponible
            if not user_question:
                return JsonResponse({"error": "Pregunta no proporcionada"}, status=400)

        if contiene_palabra_baneada(user_question.lower()):
            return JsonResponse({"error": "La pregunta contiene palabras prohibidas"}, status=400)

        menu_keyword, activar_menu = validar_pregunta(user_question)
        if activar_menu:
            return render(request, 'menu.html')

        # Maneja el campo sub_question si es necesario
        if user_question == 'problema':
            # Lógica para problema
            combined_message = f"Problema: {sub_question}" if sub_question else "Problema con la clave"
        elif user_question == 'ayuda':
            # Lógica para ayuda
            combined_message = f"Error de inicio de sesión: {sub_question}" if sub_question else "Error de inicio de sesión"
        elif user_question == 'otro':
            # Lógica para otro
            combined_message = f"Otra consulta: {sub_question}" if sub_question else "Otra consulta"
        else:
            combined_message = user_question

        try:
            response = requests.post(
                'http://localhost:5005/webhooks/rest/webhook',
                json={
                    "sender": "default",
                    "message": combined_message
                }
            )

            if response.status_code != 200:
                return JsonResponse({"error": "Error al comunicarse con el servidor de Rasa"}, status=response.status_code)
            
            rasa_response = response.json()
            if not rasa_response:
                return JsonResponse({"error": "Rasa no retornó una respuesta"}, status=500)

            return JsonResponse(rasa_response, safe=False)

        except requests.ConnectionError:
            return JsonResponse({"error": "Error de conexión con el servidor de Rasa"}, status=500)    
    return JsonResponse({"error": "Acción denegada, utilice POST"}, status=405)

@csrf_exempt
def respuestas(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip().lower()
        except json.JSONDecodeError:
            return JsonResponse({"error": "Cuerpo de solicitud inválido"}, status=400)

        if not question:
            return JsonResponse({"error": "Campo pregunta obligatorio"}, status=400)

        if contiene_palabra_baneada(question):
            return JsonResponse({"error": "La pregunta contiene palabras prohibidas"}, status=400)

        try:
            response_entries = pregunta.objects.filter(frase__iexact=question)

            if response_entries.exists():
                random_response = random.choice(response_entries)
                response = random_response.respuesta
                return JsonResponse({'response': response})
            else:
                try:
                    response = requests.post(
                        'http://localhost:5005/webhooks/rest/webhook',
                        json={
                            "sender": "default",
                            "message": question
                        }
                    )

                    if response.status_code != 200:
                        return JsonResponse({"error": "Error al comunicarse con el servidor de Rasa"}, status=response.status_code)
                    
                    rasa_response = response.json()
                    if not rasa_response:
                        return JsonResponse({"error": "Rasa no retornó una respuesta"}, status=500)

                    return JsonResponse(rasa_response, safe=False)

                except requests.ConnectionError:
                    return JsonResponse({"error": "Error de conexión con el servidor de Rasa"}, status=500)

        except Exception as e:
            print(f"Error al buscar respuesta en la base de datos: {e}")
            return JsonResponse({"error": "Error interno del servidor. Inténtalo más tarde."}, status=500)

    return JsonResponse({"error": "Método inválido. Utilice POST"}, status=405)

def menu(request):
    return render(request, 'menu.html')