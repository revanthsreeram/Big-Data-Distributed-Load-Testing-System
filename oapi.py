from fastapi import FastAPI, WebSocket
from confluent_kafka import Consumer, KafkaError
import asyncio
import json
app = FastAPI()
kafka_consumer = None  # Variable to hold the Kafka consumer
active_websocket = None  # Variable to hold the active WebSocket connection

global aggregate
aggregate = {}

async def start_kafka_consumer():
    global kafka_consumer

    if kafka_consumer is None:
        kafka_consumer = Consumer({'bootstrap.servers': 'localhost:9092', 'group.id': 'test', 'auto.offset.reset': 'latest'})
        kafka_consumer.subscribe(['metrics'])

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
            node_id = message['node_id']
            test_id = message['test_id']
            report_id = message['report_id']
            metrics = message['metrics']
            mean_latency = int(metrics['mean_latency'])
            median_latency = int(metrics['median_latency'])
            min_latency = int(metrics['min_latency'])
            max_latency = int(metrics['max_latency'])
            if test_id in aggregate.keys():
                aggregate[test_id]['latency_mean'].append(mean_latency)
                aggregate[test_id]['latency_median'].append(median_latency)
                aggregate[test_id]['latency_median'].sort()
                aggregate[test_id]['min_latency'] = min(min_latency,aggregate[test_id]['min_latency'])
                aggregate[test_id]['max_latency'] = max(max_latency,aggregate[test_id]['max_latency'])
                aggregate[test_id]['mean_latency'] = sum(aggregate[test_id]['latency_mean'])/len(aggregate[test_id]['latency_mean'])
                aggregate[test_id]['median_latency'] = aggregate[test_id]['latency_median'][len(aggregate[test_id]['latency_median'])//2]
            else:
                aggregate[test_id] = {'latency_mean' : [], 'latency_median' : [], 'min_latency' : min_latency, 'max_latency' : max_latency, 'mean_latency' : mean_latency, 'median_latency':median_latency}
                aggregate[test_id]['latency_mean'].append(mean_latency)
                aggregate[test_id]['latency_median'].append(median_latency)

            print(f"Received Kafka message: {message}")
            print(f"Aggregate is : {aggregate}")
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
@app.websocket("/ws")
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

