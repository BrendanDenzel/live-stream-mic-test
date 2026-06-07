FROM python:3.11-slim

# Install icecast
RUN apt-get update && apt-get install -y icecast2 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
COPY icecast.xml /etc/icecast2/icecast.xml

# Start both icecast and flask app
CMD icecast2 -c /etc/icecast2/icecast.xml & python app.py
