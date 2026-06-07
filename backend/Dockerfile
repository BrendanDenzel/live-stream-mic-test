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

EXPOSE 5000 8000

CMD bash -c "icecast2 -c icecast.xml & gunicorn --bind 0.0.0.0:5000 app:app"
