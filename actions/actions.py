from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionPreguntarProblema(Action):
    def name(self) -> Text:
        return "action_preguntar_problema"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
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

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get("text", "").strip()
        words = user_message.split()
        
        if not user_message:
            dispatcher.utter_message(template="utter_ask_valid_question")
        else:
            # Verificar si la mayoría de las palabras son números
            num_count = sum(1 for word in words if word.isdigit())
            if num_count / len(words) >= 0.5:  # Si más del 50% son números
                dispatcher.utter_message(template="utter_ask_invalid_number_question")
            else:
                dispatcher.utter_message("")

        return []

class MensajeEnBlanco(Action):
    def name(self) -> Text:
        return "action_mensaje_en_blanco"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get("text", "").strip()
        if not user_message:
            dispatcher.utter_message(template="utter_ask_valid_question")
        else:
            dispatcher.utter_message("")

        return []
