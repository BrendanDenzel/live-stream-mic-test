import os
from flask import Flask, request
from flask_cors import CORS
import socket
import base64

app = Flask(__name__)
CORS(app)

@app.route('/ping')
def ping():
    return 'pong', 200

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """Send audio to Icecast"""
    try:
        audio_bytes = request.data
        if len(audio_bytes) < 2:
            return {'status': 'ok'}, 200
        
        # Connect to Icecast and send audio
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8000))
        
        auth = base64.b64encode(b'source:testing123').decode()
        request_str = f"SOURCE /stream HTTP/1.0\r\nAuthorization: Basic {auth}\r\nContent-Type: audio/mpeg\r\n\r\n"
        
        sock.sendall(request_str.encode() + audio_bytes)
        sock.close()
        
        return {'status': 'ok'}, 200
    except Exception as e:
        print(f"Upload error: {e}")
        return {'error': str(e)}, 400

@app.route('/status')
def status():
    return {'status': 'running', 'icecast': 'http://localhost:8000/stream'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
