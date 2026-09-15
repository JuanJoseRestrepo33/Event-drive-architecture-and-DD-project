FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENV PYTHONPATH=/app/src BROKER=pulsar BROKER_HOST=broker PYTHONUNBUFFERED=1
EXPOSE 5002
CMD ["python", "src/pagos/main.py"]
