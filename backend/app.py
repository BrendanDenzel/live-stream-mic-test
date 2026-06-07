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
    """Stream audio as continuous live MP3"""
    def generate():
        import wave
        
        while True:
            try:
                with buffer_lock:
                    if len(audio_buffer) == 0:
                        audio_array = np.zeros(16000, dtype=np.int16)
                    else:
                        audio_array = np.array(list(audio_buffer), dtype=np.int16)
                
                # Create small WAV chunk (1 second)
                chunk_size = 16000  # 1 second at 16kHz
                audio_chunk = audio_array[-chunk_size:] if len(audio_array) >= chunk_size else audio_array
                
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(audio_chunk.tobytes())
                
                wav_buffer.seek(0)
                yield wav_buffer.read()
                
                # Send new chunk every 1 second
                import time
                time.sleep(1)
            except Exception as e:
                print(f"Stream error: {e}")
                break
    
    return Response(generate(), mimetype='audio/mpeg', headers={'Content-Type': 'audio/mpeg'})


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
