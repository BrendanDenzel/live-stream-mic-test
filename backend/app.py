import os
import socket
import base64
import requests
from flask import Flask, Response, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active Icecast sockets per client session
icecast_sockets = {}

@app.route('/ping')
def ping():
    return 'pong', 200

# ==========================================
# THIS IS WHERE THE LAST PYTHON BLOCK GOES:
# ==========================================
@app.route('/stream.mp3')
def stream_audio():
    """Proxies the internal Icecast stream to external listeners"""
    def generate():
        # Connects to the local Icecast instance running in the background
        with requests.get("http://127.0.0", stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                yield chunk
    return Response(generate(), mimetype="audio/mpeg")

# ==========================================
# WEBSOCKET EVENTS FOR THE BROADCASTER:
# ==========================================
@socketio.on('connect')
def handle_connect():
    print("Client connected via WebSocket")

@socketio.on('start-stream')
def start_stream():
    """Initializes the persistent Icecast source connection"""
    session_id = request.sid if hasattr(request, 'sid') else 'default'
    try:
        # Open persistent TCP socket to background Icecast
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 8000))
        
        # Send Icecast source authentication headers
        auth = base64.b64encode(b'source:testing123').decode()
        headers = (
            "SOURCE /stream HTTP/1.0\r\n"
            f"Authorization: Basic {auth}\r\n"
            "Content-Type: audio/mpeg\r\n"
            "Ice-Name: Live Mic Stream\r\n\r\n"
        )
        sock.sendall(headers.encode())
        
        # Save socket reference for this session
        icecast_sockets[session_id] = sock
        print("Successfully connected source to Icecast")
        emit('stream-status', {'status': 'connected'})
    except Exception as e:
        print(f"Icecast connection error: {e}")
        emit('stream-status', {'status': 'error', 'message': str(e)})

@socketio.on('audio-chunk')
def handle_audio_chunk(data):
    """Pipes continuous binary MP3 chunks directly into Icecast"""
    session_id = request.sid if hasattr(request, 'sid') else 'default'
    sock = icecast_sockets.get(session_id)
    
    if sock:
        try:
            # data is raw binary bytes from the frontend browser mic
            sock.sendall(data)
        except Exception as e:
            print(f"Error piping audio to Icecast: {e}")
            cleanup_socket(session_id)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid if hasattr(request, 'sid') else 'default'
    cleanup_socket(session_id)

def cleanup_socket(session_id):
    sock = icecast_sockets.pop(session_id, None)
    if sock:
        try:
            sock.close()
            print(f"Closed Icecast socket for session {session_id}")
        except:
            pass

if __name__ == '__main__':
    # Fallback for running locally without Gunicorn
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
