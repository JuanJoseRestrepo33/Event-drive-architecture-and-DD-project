import os
import threading

from flask import Flask

basedir = os.path.abspath(os.path.dirname(__file__))


def registrar_handlers():
    import cotizaciones.modulos.cotizaciones.aplicacion  # noqa: cablea señales *Integracion


def importar_modelos_alchemy():
    import cotizaciones.modulos.cotizaciones.infraestructura.dto  # noqa


def comenzar_consumidor(app):
    """Suscripción al tópico de comandos en un hilo (como en el tutorial)."""
    import cotizaciones.modulos.cotizaciones.infraestructura.consumidores as consumidores
    threading.Thread(target=consumidores.suscribirse_a_comandos, args=(app,), daemon=True).start()


def create_app(configuracion={}):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = '5a2c1e3f-hogar-de-los-alpes-cotizaciones'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['TESTING'] = configuracion.get('TESTING')

    from cotizaciones.config.db import init_db, database_connection
    app.config['SQLALCHEMY_DATABASE_URI'] = database_connection(configuracion, basedir=basedir)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 15}}
    init_db(app)
    from cotizaciones.config.db import db

    importar_modelos_alchemy()
    registrar_handlers()
    with app.app_context():
        db.create_all()

    if not configuracion.get('TESTING'):
        comenzar_consumidor(app)

    from . import cotizaciones as api_cotizaciones
    app.register_blueprint(api_cotizaciones.bp)

    @app.route("/health")
    def health():
        return {"status": "up", "servicio": "cotizaciones", "persistencia": "event-sourcing"}

    return app
