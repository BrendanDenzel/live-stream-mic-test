FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    icecast2 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY app.py .
COPY icecast.xml .

# Render injects the PORT env variable automatically. 
# We tell Gunicorn to use gevent workers to support WebSockets.
CMD icecast2 -c icecast.xml -b && gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT app:socketio
