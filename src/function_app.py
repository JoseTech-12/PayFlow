import azure.functions as func
import logging
import json
from azure.cosmos import CosmosClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import os

app = func.FunctionApp()

# =========================
# CONFIGURACIONES
# =========================
QUEUE_NAME = "high-priority-transactions"
DATABASE_NAME = "payflowdb"
CONTAINER_NAME = "transactions"

# =========================
# FUNCIÓN 1: VALIDAR TRANSACCIÓN (EVENT HUB TRIGGER)
# =========================
@app.event_hub_message_trigger(
    arg_name="azeventhub",
    event_hub_name="transactions",
    connection="EventHubConnectionString"
)
def validarTransaccion(azeventhub: func.EventHubEvent):
    COSMOS_CONNECTION = os.getenv("CosmosDBConnection")
    SERVICE_BUS_CONNECTION = os.getenv("ServiceBusConnection")
    
    if not COSMOS_CONNECTION:
        logging.error("❌ La variable 'CosmosDBConnection' no está configurada en el entorno.")
        return

    body = azeventhub.get_body().decode('utf-8')
    data = json.loads(body)
    logging.info(f"🟢 Nueva transacción recibida: {data.get('transaction_id')}")

    monto = data["monto"]

    # =========================
    # REGLA ANTIFRAUDE (Ajustada para pruebas)
    # =========================
    # Si vas a mandar montos pequeños en tus pruebas, baja este límite temporalmente a 1000
    if monto > 5000000:
        prioridad = "ALTA"
        sospechosa = True
    else:
        prioridad = "NORMAL"
        sospechosa = False

    transaction = {
        "id": data["transaction_id"],
        "transaction_id": data["transaction_id"],
        "comercio_id": str(data["comercio_id"]),
        "monto": monto,
        "tipo": data["tipo"],
        "estado": "VALIDADA",
        "prioridad": prioridad,
        "sospechosa": sospechosa
    }

    # =========================
    # GUARDAR EN COSMOS DB
    # =========================
    try:
        cosmos_client = CosmosClient.from_connection_string(COSMOS_CONNECTION)
        database = cosmos_client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        container.create_item(body=transaction)
        logging.info("💾 Transacción guardada con éxito en Cosmos DB.")
    except Exception as e:
        logging.error(f"❌ Error al guardar en Cosmos DB: {e}")

    # =========================
    # ENVIAR A SERVICE BUS (Estructura robusta con Autoflush)
    # =========================
    if sospechosa:
        if not SERVICE_BUS_CONNECTION:
            logging.error("❌ Transacción sospechosa detectada, pero 'ServiceBusConnection' no existe.")
            return
            
        try:
            # Forzamos a que el cliente y el remitente compartan el ciclo de vida de forma estricta
            with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION) as client:
                with client.get_queue_sender(queue_name=QUEUE_NAME) as sender:
                    message = ServiceBusMessage(json.dumps(transaction))
                    sender.send_messages(message)
                    logging.info(f"🚀 Alerta enviada con éxito a Service Bus para ID: {transaction['id']}")
        except Exception as e:
            logging.error(f"❌ Error crítico al enviar a Service Bus: {e}")


# =========================
# FUNCIÓN 2: NOTIFICAR COMERCIO (SERVICE BUS TRIGGER)
# =========================
@app.service_bus_queue_trigger(
    arg_name="mensaje",
    queue_name="high-priority-transactions",
    connection="ServiceBusConnection"
)
def notificarComercio(mensaje: func.ServiceBusMessage):
    body = mensaje.get_body().decode('utf-8')
    data = json.loads(body)

    logging.info(f"🔔 Webhook enviado al comercio {data.get('comercio_id')}")
    logging.info(f"✅ Transacción {data.get('transaction_id')} notificada correctamente.")