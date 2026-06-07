import os
import subprocess
import threading
import time
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Start Icecast in background
def start_icecast():
    try:
        # Create icecast.xml config
        icecast_config = """<icecast>
  <limits>
    <clients>100</clients>
    <sources>10</sources>
  </limits>
  <authentication>
    <source-password>testing123</source-password>
    <admin-user>admin</admin-user>
    <admin-password>admin123</admin-password>
  </authentication>
  <listen-socket>
    <port>8000</port>
    <bind-address>0.0.0.0</bind-address>
  </listen-socket>
  <mount>
    <mount-name>/stream</mount-name>
    <description>Test Stream</description>
  </mount>
</icecast>"""
        
        with open('icecast.xml', 'w') as f:
            f.write(icecast_config)
        
        # Start icecast
        subprocess.Popen(['icecast', '-c', 'icecast.xml'])
        print("Icecast started on port 8000")
    except Exception as e:
        print(f"Icecast error: {e}")

@app.route('/ping')
def ping():
    return 'pong', 200

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """Receive audio from broadcaster and send to Icecast"""
    try:
        audio_bytes = request.data
        if len(audio_bytes) < 2:
            return {'status': 'ok'}, 200
        
        # Send directly to Icecast
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8000))
        
        # Icecast SOURCE protocol
        auth = 'testing123'
        request_str = f"""SOURCE /stream HTTP/1.0\r
Authorization: Basic {__import__('base64').b64encode(f'source:{auth}'.encode()).decode()}\r
Content-Type: audio/mpeg\r
Content-Length: {len(audio_bytes)}\r
\r
"""
        sock.sendall(request_str.encode() + audio_bytes)
        sock.close()
        
        return {'status': 'ok'}, 200
    except Exception as e:
        print(f"Upload error: {e}")
        return {'error': str(e)}, 400

@app.route('/status')
def status():
    return {'status': 'running', 'icecast': 'http://localhost:8000'}, 200

# Start Icecast on app startup
threading.Thread(target=start_icecast, daemon=True).start()
time.sleep(2)  # Wait for Icecast to start

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
