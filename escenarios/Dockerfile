# Contenedor CLIENTE de los escenarios (Modo A): tiene pulsar-client y ve al
# broker y a los servicios por la red de docker-compose. Necesario en Windows,
# donde pulsar-client no tiene wheels para el host.
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pulsar-client
COPY servicios/cotizaciones/src /app/servicios/cotizaciones/src
COPY escenarios /app/escenarios
WORKDIR /app/escenarios
ENV BROKER=pulsar BROKER_HOST=broker PYTHONUNBUFFERED=1 \
    URL_COTIZACIONES=http://cotizaciones:5001 URL_PAGOS=http://pagos:5002 \
    URL_NOTIFICACIONES=http://notificaciones:5003 URL_TRABAJOS=http://trabajos:5004 URL_SAGA=http://saga:5005 \
    E7_ESTADO=/estado/e7.json
CMD ["python", "escenario_e1_escalabilidad.py"]
