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
    def __init__(self, node_id, metrics_store):
        self.node_id = node_id
        self.kafka_bootstrap_servers = 'localhost:9092'
        self.orchestrator_ip = 'localhost'
        self.producer = Producer({'bootstrap.servers': self.kafka_bootstrap_servers})
        self.consumer = Consumer({
            'bootstrap.servers': self.kafka_bootstrap_servers,
            'group.id': f'driver-group-{self.node_id}',
            'auto.offset.reset': 'latest'
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
        test_config_thread = threading.Thread(target=self.consume_test_config)
        heartbeat_thread = threading.Thread(target=self.send_heartbeat_continuously)

        test_config_thread.start()
        heartbeat_thread.start()

    def register_node(self):
        register_msg = {
            "node_id": self.node_id,
            "node_IP": self.orchestrator_ip,
            "message_type": "DRIVER_NODE_REGISTER"
        }
        self.produce_message('register1', register_msg)

    def consume_test_config(self):
        self.consumer.assign([TopicPartition('test_config', 0)])
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
                self.simulate_load_test()

    def handle_test_config(self, msg):
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

    def simulate_load_test(self):
        total_requests = self.test_config['message_count_per_driver']
        for _ in range(total_requests):
            start_time = time.time()
            response_ping = requests.get(f"http://127.0.0.1:5000/ping")
            response_metrics = requests.get(f"http://127.0.0.1:5000/metrics")
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            self.latency_values.append(latency)
            self.send_heartbeat()
            time.sleep(self.test_config['test_message_delay'])
            self.sent_requests_counter += 1

        self.send_metrics()
        #self.send_heartbeat()

    def send_metrics(self):
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
        heartbeat_msg = {
            "node_id": self.node_id,
            "heartbeat": "YES",
            "timestamp": str(datetime.datetime.now())
        }
        self.produce_message('heartbeat', heartbeat_msg)

    def produce_message(self, topic, message):
        self.producer.produce(topic, key='key', value=json.dumps(message))
        self.producer.flush()

    def send_heartbeat_continuously(self):
        while True:
            self.send_heartbeat()
            time.sleep(1)

if __name__ == "__main__":
    node_id = int(input())
    metrics_store = MetricsStore()
    driver = DriverNode(node_id, metrics_store)
    driver.run()
