import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionPreguntarProblema(Action):
    def name(self) -> Text:
        return "action_preguntar_problema"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(template="utter_preguntar_problemas")
        return []

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(template="utter_default")
        return []

class SoloNumerosYBlanco(Action):
    def name(self) -> Text:
        return "action_solo_numeros_y_blanco"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "").strip()
        words = user_message.split()
        
        if not user_message:
            dispatcher.utter_message(template="utter_ask_valid_question")
        else:
            num_count = sum(1 for word in words if word.isdigit())
            if num_count / len(words) >= 0.5:
                dispatcher.utter_message(template="utter_ask_invalid_number_question")
            else:
                dispatcher.utter_message("")
        return []

class MensajeEnBlanco(Action):
    def name(self) -> Text:
        return "action_mensaje_en_blanco"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "").strip()
        if not user_message:
            dispatcher.utter_message(template="utter_ask_valid_question")
        else:
            dispatcher.utter_message("")
        return []

class ActionGuardarRespuesta(Action):
    def name(self) -> Text:
        return "action_guardar_respuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        problem_type = tracker.get_slot("problem_type")
        question = "¿Qué tipo de problema tienes?"
        response = problem_type
        is_correct = True  # La respuesta es correcta o no

        data = {
            "question": question,
            "response": response,
            "is_correct": is_correct
        }

        response = requests.post("http://localhost:8000/rasadj/action/", data=data)

        dispatcher.utter_message(template="utter_seleccionar_problema", problem_type=problem_type)
        return []
