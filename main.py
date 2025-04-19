from flask import Flask, request

app = Flask(__name__)

@app.route('/receive', methods=['POST'])
def receive():
    data = request.json
    print("📍 Received Location:", data)
    return "Location received", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
