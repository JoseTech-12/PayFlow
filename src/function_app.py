import azure.functions as func
import logging
import json
from azure.cosmos import CosmosClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import os

app = func.FunctionApp()

# =========================
# CONFIGURACIONES (Nombres de colas y contenedores)
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
    # 1. Recuperar cadenas de conexión de forma segura DENTRO de la ejecución
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
    # REGLA ANTIFRAUDE
    # =========================
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
    # GUARDAR EN COSMOS DB (Conexión segura)
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
    # ENVIAR A SERVICE BUS
    # =========================
    if sospechosa:
        if not SERVICE_BUS_CONNECTION:
            logging.error("❌ Transacción sospechosa detectada, pero 'ServiceBusConnection' no está configurada.")
            return
            
        try:
            servicebus_client = ServiceBusClient.from_connection_string(conn_str=SERVICE_BUS_CONNECTION)
            with servicebus_client:
                sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
                with sender:
                    message = ServiceBusMessage(json.dumps(transaction))
                    sender.send_messages(message)
                    logging.info("⚠️ Alerta: Transacción de alta prioridad enviada a Service Bus.")
        except Exception as e:
            logging.error(f"❌ Error al enviar mensaje a Service Bus: {e}")


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

    logging.info(f"🔔 Webhook enviado al comercio {data['comercio_id']}")
    logging.info(f"✅ Transacción {data['transaction_id']} notificada correctamente.")