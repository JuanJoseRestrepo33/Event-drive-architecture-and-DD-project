FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENV PYTHONPATH=/app/src BROKER=pulsar BROKER_HOST=broker PYTHONUNBUFFERED=1 \
    URL_COTIZACIONES=http://cotizaciones:5001 URL_PAGOS=http://pagos:5002 \
    URL_NOTIFICACIONES=http://notificaciones:5003 URL_TRABAJOS=http://trabajos:5004 \
    URL_SAGA=http://saga:5005
EXPOSE 5000
CMD ["python", "src/bff/main.py"]
