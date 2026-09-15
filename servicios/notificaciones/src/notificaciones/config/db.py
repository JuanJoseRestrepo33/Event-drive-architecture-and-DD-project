"""Configuración de la base de datos con Flask-SQLAlchemy
(manejador de BD para persistencia y consulta, como en el tutorial)."""
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def database_connection(configuracion: dict, basedir: str) -> str:
    if configuracion.get('DB_URL'):
        return configuracion['DB_URL']
    return os.getenv('DB_URL', 'sqlite:///' + os.path.join(basedir, 'notificaciones.db'))


def init_db(app):
    db.init_app(app)
