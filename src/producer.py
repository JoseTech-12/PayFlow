from azure.eventhub import EventHubProducerClient, EventData
import json
import uuid
import random
import os

CONNECTION_STR = os.getenv("EventHubConnectionString")
EVENT_HUB_NAME = "transactions"

producer = EventHubProducerClient.from_connection_string(
    conn_str=CONNECTION_STR,
    eventhub_name=EVENT_HUB_NAME
)

evento = {
    "transaction_id": str(uuid.uuid4()),
    "comercio_id": random.randint(1, 100),
    "monto": 7000000,
    "tipo": "compra"
}

event_data_batch = producer.create_batch()
event_data_batch.add(EventData(json.dumps(evento)))

producer.send_batch(event_data_batch)

print("Evento enviado:")
print(evento)

producer.close()