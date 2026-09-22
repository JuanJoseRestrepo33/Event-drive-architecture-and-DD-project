"""El orquestador no publica eventos de integración propios: sus eventos de
dominio (EntradaSagaLog) se persisten como filas del SAGA LOG en la misma
transacción que el estado de la saga (ver comandos/base.py)."""
