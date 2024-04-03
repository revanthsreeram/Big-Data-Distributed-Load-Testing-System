from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from confluent_kafka import Consumer,Producer, KafkaError
import subprocess
import json
import threading

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
kafka_producer = Producer({'bootstrap.servers': 'localhost:9092'})
running_processes = []
id_dictionary = {}

class NumberInput(BaseModel):
    number: int

def start_subprocesses(number: int):
    global running_processes
    for i in range(1, number + 1):
        process = subprocess.Popen(['/usr/bin/python3', 'driver.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.stdin.write(f"{i}\n")
        process.stdin.flush()
        running_processes.append(process)
    
    print(f"{number} subprocesses started successfully")

def start_kafka_consumer(number: int):
    global id_dictionary

    # Kafka consumer configuration
    kafka_consumer_conf = {
        'bootstrap.servers': 'localhost:9092',  # Replace with your Kafka broker address
        'group.id': 'my-group',  # Consumer group ID
        'auto.offset.reset': 'latest'  # Start consuming from the earliest available offset
    }

    try:
        # Create Kafka Consumer
        kafka_consumer = Consumer(kafka_consumer_conf)
        kafka_consumer.subscribe(['register1'])  # Subscribe to the 'register' topic

        # Start polling messages
        while len(id_dictionary) < number:
            msg = kafka_consumer.poll(1.0)  # Poll for new messages
            print("sup")
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Kafka error: {msg.error()}")
                    continue
            print('hey')
            print(msg.value())
            message = json.loads(msg.value())
            id_attribute = message['node_id']
            if id_attribute:
                id_dictionary[id_attribute] = message.get('node_IP')  #Store in the dictionary

        kafka_consumer.close()  # Close the consumer when the required messages are received

    except Exception as e:
        print(f"Exception in Kafka consumer: {e}")

@app.post("/process_number", status_code=200)
async def process_number(number_input: NumberInput):
    number = number_input.number

    # Start a thread for subprocesses
    subprocess_thread = threading.Thread(target=start_subprocesses, args=(number,))
    subprocess_thread.start()

    # Start another thread for Kafka consumer polling
    kafka_consumer_thread = threading.Thread(target=start_kafka_consumer, args=(number,))
    kafka_consumer_thread.start()

    return 

@app.post("/send_trigger")
async def send_trigger(message: dict):
    try:
        print(message["test_type"])
        #test = json.loads(message)
        print("helo")
        kafka_producer.produce('test_config', value=json.dumps(message))
        kafka_producer.flush()
        print('yo')
        return 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.options("/process_number")
async def options_process_number():
    return {"message": "Preflight request successful"}

@app.post("/stop_processes")
async def stop_processes():
    global running_processes
    for process in running_processes:
        process.terminate()
    
    running_processes = []  # Clear the list of running processes
    print("all terminated")
    return 

