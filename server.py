from flask import Flask, jsonify, request

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Initialize counters
requests_sent = 0
responses_sent = 0

@app.route('/ping', methods=['GET'])
def ping():
    global requests_sent
    requests_sent += 1
    return "Pong!"

@app.route('/metrics', methods=['GET'])
def metrics():
    global responses_sent
    metrics_data = {
        'requests_sent': requests_sent,
        'responses_sent': responses_sent
    }
    responses_sent += 1
    
    # Print a message to the console or log the request
    print("Received a request to /metrics")

    return jsonify(metrics_data)

if __name__ == '__main__':
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(host='0.0.0.0', port=5000)
