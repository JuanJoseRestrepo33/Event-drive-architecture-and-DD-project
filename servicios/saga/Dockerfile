FROM python:3.11-slim
WORKDIR /app
# sqlite3 CLI: cliente de base de datos para consultar el SAGA LOG con SQL
RUN apt-get update -qq && apt-get install -y -qq sqlite3 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENV PYTHONPATH=/app/src BROKER=pulsar BROKER_HOST=broker PYTHONUNBUFFERED=1
EXPOSE 5005
CMD ["python", "src/saga/main.py"]
