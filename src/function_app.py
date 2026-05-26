import azure.functions as func
import logging
import json
from azure.cosmos import CosmosClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import os

app = func.FunctionApp()

# =========================
# COSMOS DB
# =========================

COSMOS_CONNECTION = os.getenv("CosmosDBConnection")

cosmos_client = CosmosClient.from_connection_string(COSMOS_CONNECTION)

database = cosmos_client.get_database_client("payflowdb")
container = database.get_container_client("transactions")

# =========================
# SERVICE BUS
# =========================

SERVICE_BUS_CONNECTION = os.getenv("ServiceBusConnection")

QUEUE_NAME = "high-priority-transactions"

# =========================
# FUNCTION
# =========================

@app.event_hub_message_trigger(
    arg_name="azeventhub",
    event_hub_name="transactions",
    connection="EventHubConnectionString"
)
def validarTransaccion(azeventhub: func.EventHubEvent):

    body = azeventhub.get_body().decode('utf-8')

    data = json.loads(body)

    logging.info("Nueva transacción recibida")

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
    # GUARDAR EN COSMOS
    # =========================

    container.create_item(body=transaction)

    logging.info("Transacción guardada en Cosmos DB")

    # =========================
    # ENVIAR A SERVICE BUS
    # =========================

    if sospechosa:

        servicebus_client = ServiceBusClient.from_connection_string(
            conn_str=SERVICE_BUS_CONNECTION
        )

        with servicebus_client:

            sender = servicebus_client.get_queue_sender(
                queue_name=QUEUE_NAME
            )

            with sender:

                message = ServiceBusMessage(json.dumps(transaction))

                sender.send_messages(message)

                logging.info(
                    "Transacción enviada a Service Bus"
                )
@app.service_bus_queue_trigger(
    arg_name="mensaje",
    queue_name="high-priority-transactions",
    connection="ServiceBusConnection"
)
def notificarComercio(mensaje: func.ServiceBusMessage):

    body = mensaje.get_body().decode('utf-8')

    data = json.loads(body)

    logging.info(
        f"Webhook enviado al comercio {data['comercio_id']}"
    )

    logging.info(
        f"Transacción {data['transaction_id']} notificada"
    )