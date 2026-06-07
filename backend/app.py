import os
from flask import Flask, request, send_file
from flask_cors import CORS
import io
import threading
from collections import deque
import numpy as np

app = Flask(__name__)
CORS(app)

# Audio buffer (stores last 30 seconds of audio)
audio_buffer = deque(maxlen=1323000)  # ~30 sec at 44.1kHz
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
    """Stream audio as MP3"""
    try:
        with buffer_lock:
            if len(audio_buffer) == 0:
                # Return silence if no audio
                silent_audio = np.zeros(44100, dtype=np.int16)
                audio_bytes = silent_audio.tobytes()
            else:
                # Convert deque to bytes
                audio_array = np.array(list(audio_buffer), dtype=np.int16)
                audio_bytes = audio_array.tobytes()
        
        # Return as WAV (simpler than MP3)
        import wave
        wav_buffer = io.BytesIO()
        
        sample_rate = 16000
        with wave.open(wav_buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(audio_bytes)
        
        wav_buffer.seek(0)
        
        return send_file(
            wav_buffer,
            mimetype='audio/wav',
            as_attachment=False,
            download_name='stream.wav'
        )
    except Exception as e:
        print(f"Stream error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}, 500

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
