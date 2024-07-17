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

@csrf_exempt
def rasa_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = data.get('user')
            user_question = data.get('question')
            if not user_question:
                return JsonResponse({"error": "Pregunta no proporcionada"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Cuerpo de solicitud inválido"}, status=400)

        # Verificar palabras prohibidas
        question_normalized = normalizar_texto(user_question)
        palabras_baneadas = palabrabaneada.objects.values_list('palabra', flat=True)
        palabras_baneadas_normalizadas = [normalizar_texto(palabra) for palabra in palabras_baneadas]

        if any(palabra_normalizada in question_normalized for palabra_normalizada in palabras_baneadas_normalizadas):
            return JsonResponse({
                "error": "Tu pregunta contiene palabras inapropiadas y no soporto ese lenguaje."
            }, status=403)

        try:
            response = requests.post(
                'http://localhost:5005/webhooks/rest/webhook',
                json={"sender": user, "message": user_question}
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
            return JsonResponse({
                "error": "Cuerpo de solicitud inválido"
            }, status=400)

        if not question:
            return JsonResponse({
                "error": "Campo pregunta obligatorio"
            }, status=400)

        # Verificar palabras prohibidas
        question_normalized = normalizar_texto(question)
        palabras_baneadas = palabrabaneada.objects.values_list('palabra', flat=True)
        palabras_baneadas_normalizadas = [normalizar_texto(palabra) for palabra in palabras_baneadas]

        if any(palabra_normalizada in question_normalized for palabra_normalizada in palabras_baneadas_normalizadas):
            return JsonResponse({
                "error": "Tu pregunta contiene palabras inapropiadas y no soporto ese lenguaje."
            }, status=403)

        try:
            response_entries = pregunta.objects.filter(frase__iexact=question_normalized)

            if response_entries.exists():
                random_response = random.choice(response_entries)
                response = random_response.respuesta
                return JsonResponse({'response': response})
            else:
                return JsonResponse({
                    "error": "Lo siento, no tengo una respuesta para esa pregunta."
                }, status=404)

        except Exception as e:
            print(f"Error al buscar respuesta: {e}")
            return JsonResponse({
                "error": "Error interno del servidor. Inténtalo más tarde."
            }, status=500)

    return JsonResponse({"error": "Método inválido. Utilice POST"}, status=405)
