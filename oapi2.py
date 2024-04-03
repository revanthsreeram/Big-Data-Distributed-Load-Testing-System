from fastapi import FastAPI, WebSocket
from confluent_kafka import Consumer, KafkaError
import asyncio
import json

app = FastAPI()
kafka_consumer = None  # Variable to hold the Kafka consumer
active_websocket = None  # Variable to hold the active WebSocket connection

async def start_kafka_consumer():
    global kafka_consumer

    if kafka_consumer is None:
        kafka_consumer = Consumer({'bootstrap.servers': 'localhost:9092', 'group.id': 'heart', 'auto.offset.reset': 'latest'})
        kafka_consumer.subscribe(['heartbeat'])

    while True:
        print("Polling Kafka")
        msg = kafka_consumer.poll(2.0)

        if msg is None:
            await asyncio.sleep(1)
            continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                await asyncio.sleep(1)
                continue
            else:
                raise KafkaError(msg.error())
        else:
            message = json.loads(msg.value())
            print(f"Received Kafka message: {message}")
            await send_to_websocket(message)

async def send_to_websocket(message):
    global active_websocket

    if active_websocket:
        try:
            print("message sending")
            await active_websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message to WebSocket: {e}")
            await close_websocket()

async def close_websocket():
    global active_websocket
    if active_websocket:
        await active_websocket.close()
        active_websocket = None

# WebSocket route
@app.websocket("/ws2")
async def websocket_endpoint(websocket: WebSocket):
    global active_websocket

    print("WebSocket connection requested")
    await websocket.accept()
    print(f"WebSocket connected: {websocket}")

    active_websocket = websocket

    try:
        kafka_task = asyncio.create_task(start_kafka_consumer())
        while True:
            if kafka_task.done():
                break
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Exception while starting Kafka consumer: {e}")
        await close_websocket()
        kafka_task.cancel()

    try:
        while True:
            await asyncio.sleep(1)  # Keep the WebSocket connection alive
    except Exception:
        await close_websocket()
        print("WebSocket disconnected")

