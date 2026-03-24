FROM python:3.11-slim

# System dependencies for Pillow and pillow-heif
RUN apt-get update && apt-get install -y \
    libheif-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV PORT=8080

CMD ["python", "main.py"]
