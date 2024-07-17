import sqlite3
import random
import re
from unidecode import unidecode
import threading
from difflib import get_close_matches
import spacy

nlp = spacy.load("es_core_news_lg")

# Normaliza el texto usando spaCy
def normalizar_texto_spacy(texto):
    doc = nlp(texto)
    tokens = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)

# Función para probar spaCy
def probar_spacy():
    textos_de_prueba = [
        "Hola, ¿cómo estás?",
        "¿Cuál es tu nombre?",
        "Estoy aprendiendo a usar spaCy.",
        "Quiero mejorar mi chatbot con NLP.",
        "El carlos deberia ver como este codigo logra funcionar"
    ]
    
    for texto in textos_de_prueba:
        normalizado = normalizar_texto_spacy(texto)
        print(f"Texto original: {texto}")
        print(f"Texto normalizado: {normalizado}\n")

# Función para obtener una conexión a la base de datos en la ruta especificada
def obtener_conexion():
    try:
        db_path = "C:\\Users\\joset\\OneDrive\\Escritorio\\Trabajo\\datosdj.db"
        return sqlite3.connect(db_path)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

# Evento de señalización para la actividad del usuario
actividad_event = threading.Event()

# Lista de palabras prohibidas
ban = ["idiota", "estúpido", "imbécil", "inútil", "tonto", "shit", "bullshit", "ctm", "conchetumadre", "concha", "pene", "vagina", "conchadetumadre"]

# Umbral de similitud para cerrar la conexión
umbral_similitud = 0.2

# Variable para controlar la advertencia por inactividad
advertencia_mostrada = False

# Función para gestionar el temporizador de inactividad
def timeout_input(prompt, timeout=180, warning_time=60):
    global advertencia_mostrada
    print(prompt, end='', flush=True)
    result = [None]

    def on_input():
        try:
            result[0] = input()
        except EOFError:
            result[0] = None
        finally:
            actividad_event.set()  # Señala que se ha recibido entrada del usuario

    thread = threading.Thread(target=on_input)
    thread.daemon = True
    thread.start()

    actividad_event.clear()  # Asegura que el evento esté inicialmente limpio

    if not actividad_event.wait(warning_time):  # Espera el tiempo de advertencia
        print(f"\n¿Hola, sigues ahí? La sesión se cerrará en {timeout - warning_time} segundos si no respondes.")
        advertencia_mostrada = True
    
    if not actividad_event.wait(timeout - warning_time):  # Espera el tiempo restante
        print("\nNo se recibió ninguna respuesta, espero haberte ayudado. La sesión se ha cerrado por inactividad.")
        return None
    
    thread.join()  # Asegura que el hilo de entrada haya terminado
    return result[0]

# Función para ejecutar consultas en la base de datos
def ejecutar_consulta(query, params=(), fetchall=True):
    with obtener_conexion() as conn:
        if conn is None:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall() if fetchall else cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error en la consulta: {e}")
            return None

def crear_base_datos():
    query_preguntas = '''
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frase TEXT NOT NULL,
            respuesta TEXT NOT NULL,
            UNIQUE(frase, respuesta)
        )
    '''
    query_ban = '''
        CREATE TABLE IF NOT EXISTS ban (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palabra TEXT NOT NULL UNIQUE
        )
    '''
    ejecutar_consulta(query_preguntas, fetchall=False)
    ejecutar_consulta(query_ban, fetchall=False)
    
    # Insertar palabras prohibidas en la tabla de ban
    for palabra in ban:
        insertar_palabra_ban(palabra)

def insertar_palabra_ban(palabra):
    query = "INSERT INTO ban (palabra) VALUES (?) ON CONFLICT(palabra) DO NOTHING"
    ejecutar_consulta(query, (palabra,), fetchall=False)

def insertar_respuesta(frase, respuesta):
    query = "INSERT INTO preguntas (frase, respuesta) VALUES (?, ?) ON CONFLICT(frase, respuesta) DO NOTHING"
    ejecutar_consulta(query, (frase, respuesta), fetchall=False)

def insertar_respuestas_iniciales():
    respuestas_iniciales = [
        ('quien es tu creador', 'Mi creador es muy tímido para decir su nombre'),
        ('adios', '¡Hasta luego! Espero haberte ayudado.'),
        ('como te llamas', 'Me llamo Lyra. Dejame ayudarte con tu consulta')
    ]
    
    nuevas_respuestas_multiples = {
        "hola": ["Hola, ¿En qué te ayudo?", "Buenos días ¿Qué necesitas?"],
        "que puedes hacer": ["Puedo responder preguntas y dudas que tengas sobre la página web.", "Ayudarte a resolver tus problemas con la página"],
        "cual es tu nombre": ["Hola, Soy Lyra.", "Soy Lyra.", "mi nombre es Lyra"],
        "muchas gracias": ["De nada. Lyra fue creada para ayudarte"],
    }

    for frase, respuesta in respuestas_iniciales:
        insertar_respuesta(frase, respuesta)
    for pregunta, respuestas in nuevas_respuestas_multiples.items():
        for respuesta in respuestas:
            insertar_respuesta(pregunta, respuesta)

# Eliminar duplicados de la base de datos
def eliminar_duplicados():
    query = '''
        DELETE FROM preguntas
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM preguntas
            GROUP BY frase, respuesta
        );
    '''
    ejecutar_consulta(query, fetchall=False)

# Manejo de respuestas múltiples
respuestas_multiples = {
    "cual es tu nombre": ["Hola, Soy Lyra.", "Soy Lyra.", "mi nombre es Lyra"],
    "hola": ["Hola, ¿En qué te ayudo?", "Buenos días ¿Qué necesitas?"],
    "que puedes hacer": ["Puedo responder preguntas y dudas que tengas sobre la página web.", "Ayudarte a resolver tus problemas con la página"],
}

# Memoria de respuestas dadas
respuestas_dadas = {}

def almacenar_respuesta(frase, respuesta):
    insertar_respuesta(frase, respuesta)

def almacenar_palabra_ban(palabra):
    insertar_palabra_ban(palabra)

def encontrar_pregunta_similar(mensaje_normalizado):
    frases = [fila[0] for fila in ejecutar_consulta("SELECT frase FROM preguntas")]
    coincidencias = get_close_matches(mensaje_normalizado, frases, n=1, cutoff=0.4)
    return coincidencias[0] if coincidencias else None

def calcular_similitud_ban(mensaje_normalizado):
    palabras = mensaje_normalizado.split()
    cantidad_palabras_ban = sum(1 for palabra in palabras if palabra in ban)
    return cantidad_palabras_ban / len(palabras) if palabras else 0

# Memoria para evitar repetir respuestas consecutivas
respuestas_anteriores = {}

def responder(mensaje):
    global advertencia_mostrada
    mensaje_normalizado = normalizar_texto_spacy(mensaje)
    conn = obtener_conexion()
    if conn is None:
        return "Lo siento, ha ocurrido un error."

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT respuesta FROM preguntas WHERE frase = ?", (mensaje_normalizado,))
        resultado = cursor.fetchall()

        if resultado:
            respuestas = [r[0] for r in resultado]
            respuesta = random.choice(respuestas)
            while respuesta == respuestas_anteriores.get(mensaje_normalizado):
                respuesta = random.choice(respuestas)
            respuestas_anteriores[mensaje_normalizado] = respuesta
            return respuesta
        elif mensaje_normalizado in respuestas_multiples:
            respuestas = respuestas_multiples[mensaje_normalizado]
            respuesta = random.choice(respuestas)
            while respuesta == respuestas_anteriores.get(mensaje_normalizado):
                respuesta = random.choice(respuestas)
            respuestas_anteriores[mensaje_normalizado] = respuesta
            return respuesta
        elif mensaje_normalizado in respuestas_dadas:
            respuesta = respuestas_dadas[mensaje_normalizado]
            while respuesta == respuestas_anteriores.get(mensaje_normalizado):
                respuesta = random.choice(respuestas)
            respuestas_anteriores[mensaje_normalizado] = respuesta
            return respuesta
        else:
            pregunta_similar = encontrar_pregunta_similar(mensaje_normalizado)
            if pregunta_similar:
                cursor.execute("SELECT respuesta FROM preguntas WHERE frase = ?", (pregunta_similar,))
                resultado = cursor.fetchall()
                respuestas = [r[0] for r in resultado]
                respuesta = random.choice(respuestas)
                while respuesta == respuestas_anteriores.get(mensaje_normalizado):
                    respuesta = random.choice(respuestas)
                respuestas_anteriores[mensaje_normalizado] = respuesta
                return respuesta
            else:
                similitud_ban = calcular_similitud_ban(mensaje_normalizado)
                
                if similitud_ban >= umbral_similitud:
                    return "No tolero ese tipo de lenguaje. La conexión se ha cerrado."
                else:
                    if advertencia_mostrada:
                        advertencia_mostrada = False
                        return "Qué bueno que sigas aquí. Lyra se estaba preocupando."
                    else:
                        nueva_respuesta = input("No sé cómo responder a eso. ¿Puedes enseñarme?\n> ")
                        almacenar_respuesta(mensaje_normalizado, nueva_respuesta)
                        respuestas_anteriores[mensaje_normalizado] = nueva_respuesta
                        return nueva_respuesta

    except sqlite3.Error as e:
        print(f"Error al responder: {e}")
        return "Lo siento, ha ocurrido un error."
    finally:
        conn.close()

print("¡Hola! Soy Lyra tu chatbot. ¿En qué puedo ayudarte?")

# Crear la base de datos y configurarla
crear_base_datos()
insertar_respuestas_iniciales()
eliminar_duplicados()

# Probar spaCy
probar_spacy()

while True:
    mensaje_usuario = timeout_input("> ")
    if mensaje_usuario is None:
        print("La sesión se ha cerrado por inactividad.")
        break
    if mensaje_usuario:  # Verifica si hay entrada del usuario
        respuesta = responder(mensaje_usuario)
        print(respuesta)

        if respuesta == "No tolero ese tipo de lenguaje. La conexión se ha cerrado." or respuesta == "La sesión se ha cerrado por inactividad." or respuesta == "¡Hasta luego! Espero haberte ayudado.":
            break
