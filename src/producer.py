import os
import json
import uuid
import random
import time
import asyncio
from azure.eventhub.aio import EventHubProducerClient  # Cambiado a cliente Asíncrono
from azure.eventhub import EventData

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

# --- CONFIGURACIÓN DE LA PRUEBA DE CARGA ---
# Modifica este número según el objetivo de la prueba (40 para base, 500 para picos estacionales)
TX_PER_SECOND = 40  

def generar_evento_por_tipo(tipo_tx):
    """
    Genera la estructura del evento según los requerimientos del caso de estudio.
    """
    tx_id = str(uuid.uuid4())
    comercio = random.randint(1, 100)
    
    if tipo_tx == "NORMAL":
        return {
            "transaction_id": tx_id,
            "comercio_id": comercio,
            "monto": random.randint(20000, 450000),
            "tipo": "compra"
        }
        
    elif tipo_tx == "ALTO_VALOR":
        return {
            "transaction_id": tx_id,
            "comercio_id": comercio,
            "monto": random.randint(5500000, 9000000),
            "tipo": "compra"
        }
        
    elif tipo_tx == "INVALIDO":
        opcion_falla = random.choice([1, 2, 3])
        if opcion_falla == 1:
            return {
                "transaction_id": tx_id,
                "comercio_id": comercio,
                "tipo": "compra"
            }
        elif opcion_falla == 2:
            return {
                "transaction_id": tx_id,
                "comercio_id": comercio,
                "monto": "SETEMILLONES_CORRUPTO",
                "tipo": "compra"
            }
        else:
            return "TEXTO_CORRUPTO_NON_JSON_A1B2C3"

async def iniciar_prueba_de_carga():
    # Inicializamos el cliente asíncrono dentro del contexto del loop de asyncio
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR,
        eventhub_name=EVENT_HUB_NAME
    )
    
    async with producer:
        print(f"\n🚀 PROBANDO INGESTA PAYFLOW: Iniciando envío continuo de {TX_PER_SECOND} tx/s...")
        print("Presiona Ctrl + C para detener la simulación de carga.\n")
        
        contador_total = 0
        tipos_disponibles = ["NORMAL", "ALTO_VALOR", "INVALIDO"]
        # Probabilidades de generación: 85% normales, 10% alto valor, 5% inválidos
        pesos_distribucion = [0.85, 0.10, 0.05] 
        
        while True:
            start_time = time.time()
            
            try:
                # Creamos el lote asíncrono para este segundo en particular
                event_data_batch = await producer.create_batch()
                
                # Llenamos el lote con el número exacto de tx especificadas por segundo
                for _ in range(TX_PER_SECOND):
                    tipo_seleccionado = random.choices(tipos_disponibles, weights=pesos_distribucion, k=1)[0]
                    evento = generar_evento_por_tipo(tipo_seleccionado)
                    
                    if isinstance(evento, dict):
                        datos_a_enviar = json.dumps(evento)
                    else:
                        datos_a_enviar = evento
                        
                    event_data_batch.add(EventData(datos_a_enviar))
                
                # Enviamos el lote completo a Azure de golpe de forma eficiente
                await producer.send_batch(event_data_batch)
                
                contador_total += TX_PER_SECOND
                print(f"📦 Lote de {TX_PER_SECOND} eventos enviado exitosamente. Total acumulado: {contador_total} tx.")
                
            except Exception as e:
                print(f"❌ Error durante el envío del lote: {e}")
            
            # Control preciso del tiempo para garantizar que se envíe exactamente cada 1 segundo
            elapsed_time = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed_time)
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        asyncio.run(iniciar_prueba_de_carga())
    except KeyboardInterrupt:
        print("\n🔒 Simulación finalizada de forma controlada por el usuario.")
        print("Conexiones con Azure cerradas con éxito.")