from confluent_kafka import Producer, Consumer, KafkaError, TopicPartition
import json
import threading
import uuid
import requests
import time
import datetime
import socket 

class MetricsStore:
    def __init__(self):
        self.metrics = {}

    def add_metrics(self, node_id, test_id, report_id, metrics):
        if node_id not in self.metrics:
            self.metrics[node_id] = {}

        if test_id not in self.metrics[node_id]:
            self.metrics[node_id][test_id] = {}

        self.metrics[node_id][test_id][report_id] = metrics

    def get_metrics(self, node_id, test_id, report_id):
        return self.metrics.get(node_id, {}).get(test_id, {}).get(report_id, {})

class DriverNode:
    def __init__(self, node_id,metrics_store):
        # self.node_id = int(input())
        self.node_id = node_id
        self.kafka_bootstrap_servers = 'localhost:9092'
        self.orchestrator_ip = 'localhost'
        self.producer = Producer({'bootstrap.servers': self.kafka_bootstrap_servers})
        self.consumer = Consumer({
        'bootstrap.servers': self.kafka_bootstrap_servers,
        'group.id': f'driver-group-{self.node_id}',
        'auto.offset.reset': 'latest'  # Change this line
        })
        self.load_test_started = threading.Event()
        self.test_config = {}
        self.sent_requests_counter = 0
        self.latency_values = []
        self.metrics_store = metrics_store
        self.source_port = 9000 + node_id
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('0.0.0.0', self.source_port))

    def run(self):
        self.register_node()
        self.consume_test_config()
        # print("Driver node is running!")
        # self.simulate_load_test()

        

    def register_node(self):
        # print("register is running!")
        register_msg = {
            "node_id": self.node_id,
            "node_IP": self.orchestrator_ip,
            "message_type": "DRIVER_NODE_REGISTER"
        }
        self.produce_message('register1', register_msg)

    def consume_test_config(self):
        # print("consume is running!")
        self.consumer.assign([TopicPartition('test_config',0)])
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break
            topic = msg.topic()
            message = json.loads(msg.value())

            if topic == 'test_config':
                self.handle_test_config(message)
                # self.start_test()
                self.simulate_load_test()

            # break

    def handle_test_config(self, msg):
        # print(msg)
        self.test_config = {}
        self.sent_requests_counter = 0
        self.latency_values = []
        test_id = int(msg["test_id"])
        test_type = msg["test_type"]
        test_message_delay = int(msg["test_message_delay"])
        message_count_per_driver = int(msg["message_count_per_driver"])
        self.test_config = {
            "test_id": test_id,
            "test_type": test_type,
            "test_message_delay": test_message_delay,
            "message_count_per_driver": message_count_per_driver
        }
        
    
    # def start_test(self):
    #     self.load_test_started.set()

    def simulate_load_test(self):
        # print("simulate is running!")
        # self.load_test_started.wait()

        total_requests = self.test_config['message_count_per_driver']

        for _ in range(total_requests):
            start_time = time.time()

        # Send a GET request to the '/ping' endpoint
            response_ping = requests.get(f"http://127.0.0.1:5000/ping")

        # Send a GET request to the '/metrics' endpoint
            response_metrics = requests.get(f"http://127.0.0.1:5000/metrics")

            end_time = time.time()

            latency = (end_time - start_time) * 1000
            self.latency_values.append(latency)

            # print("Before send_metrics")
            # self.send_metrics()
            # print("After send_metrics")

            # print("Before send_heartbeat")
            self.send_heartbeat()
            # print("After send_heartbeat")

            # print(f"Sent {self.sent_requests_counter + 1} requests")

            # if self.test_config['test_type'] == "TSUNAMI" and self.test_config['test_message_delay'] > 0:
            #     time.sleep(self.test_config['test_message_delay'])
            # elif self.test_config['test_type'] == "AVALANCHE":
            #     pass
            # else:
            #     time.sleep(sleep_interval)
            time.sleep(self.test_config['test_message_delay'])

            self.sent_requests_counter += 1

        # print("Finished sending requests")

        # print(f"Sent {self.sent_requests_counter} requests")

        # print("Before final send_metrics")
        self.send_metrics()
        # print("After final send_metrics")

        # print("Before final send_heartbeat")
        self.send_heartbeat()
        # print("After final send_heartbeat")


    def send_metrics(self):
        # print("metrics is running!")
        metrics_msg = {
            "node_id": self.node_id,
            "test_id": self.test_config['test_id'],
            "report_id": str(uuid.uuid4()),
            "metrics": {
                "mean_latency": self.calculate_mean_latency(),
                "median_latency": self.calculate_median_latency(),
                "min_latency": min(self.latency_values),
                "max_latency": max(self.latency_values)
            }
        }

        self.metrics_store.add_metrics(self.node_id, self.test_config['test_id'], metrics_msg['report_id'],
                                       metrics_msg['metrics'])
        # print(f"Sending metrics to topic 'metrics': {metrics_msg}")

        self.produce_message('metrics', metrics_msg)


    def calculate_mean_latency(self):
        return sum(self.latency_values) / len(self.latency_values) if self.latency_values else 0

    def calculate_median_latency(self):
        sorted_latencies = sorted(self.latency_values)
        mid = len(sorted_latencies) // 2
        if len(sorted_latencies) % 2 == 0:
            lower_mid = sorted_latencies[mid - 1]
            upper_mid = sorted_latencies[mid]
            return (lower_mid + upper_mid) / 2.0
        else:
            return sorted_latencies[mid] if self.latency_values else 0

    def send_heartbeat(self):
        # print("heartbeat is running!")
        heartbeat_msg = {
            "node_id": self.node_id,
            "heartbeat": "YES",
            "timestamp": str(datetime.datetime.now())
        }

        self.produce_message('heartbeat', heartbeat_msg)

    def produce_message(self, topic, message):
        # print("producer is running!")
        self.producer.produce(topic, key='key', value=json.dumps(message))
        self.producer.flush()

if __name__ == "__main__":
    # import sys

    # if len(sys.argv) != 4:
    #     print("Usage: python driver_node.py <node_id> <kafka_bootstrap_servers> <orchestrator_ip>")
    #     sys.exit(1)

    # driver_node_id, kafka_bootstrap_servers, orchestrator_ip = sys.argv[1], sys.argv[2], sys.argv[3]
    node_id = int(input())

    metrics_store = MetricsStore()

    driver = DriverNode(node_id,metrics_store)
    
    driver.run()
