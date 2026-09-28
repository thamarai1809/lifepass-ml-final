FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-tam && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install \
    --default-timeout=300 \
    --retries 10 \
    --no-cache-dir \
    -r requirements.txt

COPY . .

RUN mkdir -p uploads

EXPOSE 10000

CMD ["sh", "-c", "streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true"]