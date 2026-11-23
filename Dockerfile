FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-liberation fonts-dejavu-core fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DATA_DIR=/srv/data
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
