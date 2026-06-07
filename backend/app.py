import os
from flask import Flask, request, send_file, Response
from flask_cors import CORS
import io
import threading
from collections import deque
import numpy as np

app = Flask(__name__)
CORS(app)

# Audio buffer (stores last 30 seconds of audio)
audio_buffer = deque(maxlen=480000)  # ~30 sec at 16kHz
buffer_lock = threading.Lock()

@app.route('/ping')
def ping():
    return 'pong', 200

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """Receive audio chunks from broadcaster"""
    try:
        audio_bytes = request.data
        if len(audio_bytes) < 2:
            return {'status': 'ok'}, 200
        
        # Convert bytes to int16 array
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        
        with buffer_lock:
            for sample in audio_int16:
                audio_buffer.append(sample)
        
        return {'status': 'ok', 'samples': len(audio_int16)}, 200
    except Exception as e:
        print(f"Upload error: {e}")
        return {'error': str(e)}, 400

@app.route('/stream.mp3')
def stream():
    """Stream audio as continuous live PCM"""
    def generate():
        last_size = 0
        
        while True:
            try:
                with buffer_lock:
                    current_size = len(audio_buffer)
                    if current_size == 0:
                        audio_array = np.zeros(16000, dtype=np.int16)
                    else:
                        audio_array = np.array(list(audio_buffer), dtype=np.int16)
                
                # Only send new audio since last chunk
                if current_size > last_size:
                    new_audio = audio_array[last_size:]
                    yield new_audio.tobytes()
                    last_size = current_size
                else:
                    # Send silence if nothing new
                    silence = np.zeros(16000, dtype=np.int16)
                    yield silence.tobytes()
                
                import time
                time.sleep(0.5)
            except Exception as e:
                print(f"Stream error: {e}")
                break
    
    return Response(generate(), mimetype='audio/mpeg')


@app.route('/status')
def status():
    """Check backend status"""
    with buffer_lock:
        buffer_size = len(audio_buffer)
    return {
        'status': 'running',
        'buffer_samples': buffer_size,
        'buffer_seconds': buffer_size / 16000
    }, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
