import os
import json
import uuid
import random
from azure.eventhub import EventHubProducerClient, EventData

# --- BLOQUE OPTIMIZADO PARA BUSCAR LOCAL.SETTINGS.JSON ---
# Opción A: Buscar una carpeta arriba (Raíz del proyecto)
ruta_padre = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
# Opción B: Buscar en la misma carpeta (Por si está dentro de /src)
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

# --------------------------------------------

# Ahora os.getenv ya podrá leer la conexión perfectamente
CONNECTION_STR = os.getenv("EventHubConnectionString")
EVENT_HUB_NAME = "transactions"

if not CONNECTION_STR:
    raise ValueError("❌ Error: 'EventHubConnectionString' no se encontró en el entorno ni en local.settings.json")

# Inicializamos el cliente de Event Hub
producer = EventHubProducerClient.from_connection_string(
    conn_str=CONNECTION_STR,
    eventhub_name=EVENT_HUB_NAME
)

# Creamos el evento de prueba
evento = {
    "transaction_id": str(uuid.uuid4()),
    "comercio_id": random.randint(1, 100),
    "monto": 7000000,
    "tipo": "compra"
}

try:
    # Creamos el lote de datos
    event_data_batch = producer.create_batch()
    
    # Convertimos el diccionario a JSON string y lo agregamos al lote
    event_data_batch.add(EventData(json.dumps(evento)))
    
    # Enviamos el lote al Event Hub
    producer.send_batch(event_data_batch)
    
    print("🚀 Evento enviado con éxito:")
    print(json.dumps(evento, indent=4))

except Exception as e:
    print(f"❌ Ocurrió un error al enviar el evento: {e}")

finally:
    # Garantizamos que la conexión se cierre pase lo que pase
    producer.close()
    print("🔒 Conexión con Event Hub cerrada.")