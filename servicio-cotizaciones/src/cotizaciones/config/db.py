"""Configuración de la base de datos con Flask-SQLAlchemy.

Manejador de BD real (PostgreSQL) para persistencia y consulta, como exige
el enunciado de la Entrega 3. La URL se resuelve por variable de entorno
para no incrustar credenciales ni acoplar el código a un motor concreto:
cambiar de motor es un cambio de configuración/infraestructura, no de
dominio ni de aplicación (inversión de dependencias).
"""
import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

DB_URL_POR_DEFECTO = 'postgresql+psycopg2://hda:hda@localhost:5432/cotizaciones'


def database_connection(configuracion: dict, basedir: str) -> str:
    if configuracion.get('DB_URL'):
        return configuracion['DB_URL']
    return os.getenv('DB_URL', DB_URL_POR_DEFECTO)


def init_db(app):
    db.init_app(app)
