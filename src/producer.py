import os
import json
import uuid
import random
import time
from azure.eventhub import EventHubProducerClient, EventData

# --- BLOQUE OPTIMIZADO PARA BUSCAR LOCAL.SETTINGS.JSON ---
ruta_padre = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
ruta_local = os.path.join(os.path.dirname(__file__), 'local.settings.json')

ruta_final = None
if os.path.exists(ruta_padre):
    ruta_final = ruta_padre
elif os.path.exists(ruta_local):
    ruta_final = ruta_local

if ruta_final:
    print(f"✅ Cargando configuración desde: {os.path.basename(ruta_final)}")
    with open(ruta_final, 'r', encoding='utf-8') as f:
        settings = json.load(f)
        values = settings.get("Values", {})
        for key, value in values.items():
            os.environ[key] = value
else:
    print("⚠️ Advertencia: No se encontró local.settings.json en ninguna de las rutas esperadas.")
# --------------------------------------------------------

CONNECTION_STR = os.getenv("EventHubConnectionString")
EVENT_HUB_NAME = "transactions"

if not CONNECTION_STR:
    raise ValueError("❌ Error: 'EventHubConnectionString' no se encontró en el entorno ni en local.settings.json")

# Inicializamos el cliente de Event Hub
producer = EventHubProducerClient.from_connection_string(
    conn_str=CONNECTION_STR,
    eventhub_name=EVENT_HUB_NAME
)

def generar_evento_por_tipo(tipo_tx):
    """
    Genera la estructura del evento según los requerimientos del caso.
    """
    tx_id = str(uuid.uuid4())
    comercio = random.randint(1, 100)
    
    if tipo_tx == "NORMAL":
        # Transacción estándar (Monto bajo, ej: entre 20,000 y 450,000 COP)
        return {
            "transaction_id": tx_id,
            "comercio_id": comercio,
            "monto": random.randint(20000, 450000),
            "tipo": "compra"
        }
        
    elif tipo_tx == "ALTO_VALOR":
        # Transacción de alto valor (Sospechosa / Alerta Antifraude > 5M COP)
        return {
            "transaction_id": tx_id,
            "comercio_id": comercio,
            "monto": random.randint(5500000, 9000000),
            "tipo": "compra"
        }
        
    elif tipo_tx == "INVALIDO":
        # Formato corrupto/inválido de forma aleatoria para probar resiliencia
        opcion_falla = random.choice([1, 2, 3])
        if opcion_falla == 1:
            # Caso A: Falta el campo obligatorio 'monto'
            return {
                "transaction_id": tx_id,
                "comercio_id": comercio,
                "tipo": "compra"
            }
        elif opcion_falla == 2:
            # Caso B: El monto no es un número (String corrupto)
            return {
                "transaction_id": tx_id,
                "comercio_id": comercio,
                "monto": "SETEMILLONES_CORRUPTO",
                "tipo": "compra"
            }
        else:
            # Caso C: JSON completamente malformado (Texto plano roto)
            return "TEXTO_CORRUPTO_NON_JSON_A1B2C3"

try:
    # Definimos los 3 tipos solicitados por el enunciado
    tipos_disponibles = ["NORMAL", "ALTO_VALOR", "INVALIDO"]
    
    # Seleccionamos uno aleatoriamente para esta ejecución
    tipo_seleccionado = random.choice(tipos_disponibles)
    print(f"\n🎲 Seleccionando escenario de prueba: [{tipo_seleccionado}]")
    
    evento = generar_evento_por_tipo(tipo_seleccionado)
    
    # Creamos el lote de datos
    event_data_batch = producer.create_batch()
    
    # Convertimos a JSON string excepto si ya es un string corrupto plano (Caso C)
    if isinstance(evento, dict):
        datos_a_enviar = json.dumps(evento)
    else:
        datos_a_enviar = evento
        
    # Agregamos al lote y enviamos
    event_data_batch.add(EventData(datos_a_enviar))
    producer.send_batch(event_data_batch)
    
    print("🚀 Evento enviado con éxito al Event Hub:")
    if isinstance(evento, dict):
        print(json.dumps(evento, indent=4))
    else:
        print(f"   String crudo enviado: {evento}")

except Exception as e:
    print(f"❌ Ocurrió un error al enviar el evento: {e}")

finally:
    producer.close()
    print("🔒 Conexión con Event Hub cerrada.")