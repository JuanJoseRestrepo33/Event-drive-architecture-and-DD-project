import os

from flask import Flask, jsonify

basedir = os.path.abspath(os.path.dirname(__file__))


def registrar_handlers():
    import cotizaciones.modulos.cotizaciones.aplicacion  # noqa: señales integración
    import cotizaciones.modulos.pagos.aplicacion         # noqa: señales dominio


def importar_modelos_alchemy():
    import cotizaciones.modulos.cotizaciones.infraestructura.dto  # noqa
    import cotizaciones.modulos.pagos.infraestructura.dto         # noqa


def comenzar_consumidor(app):
    """Suscripción a tópicos del broker en hilos (como en el tutorial).
    Solo se activa con BROKER_HOST definido (requiere Pulsar corriendo)."""
    import threading
    import cotizaciones.modulos.cotizaciones.infraestructura.consumidores as cotizaciones_consumidores

    threading.Thread(target=cotizaciones_consumidores.suscribirse_a_eventos, daemon=True).start()
    threading.Thread(target=cotizaciones_consumidores.suscribirse_a_comandos, daemon=True).start()


def create_app(configuracion={}):
    app = Flask(__name__, instance_relative_config=True)

    app.secret_key = '5a2c1e3f-hogar-de-los-alpes-cotizaciones'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['TESTING'] = configuracion.get('TESTING')

    # Inicializa la DB
    from cotizaciones.config.db import init_db, database_connection
    app.config['SQLALCHEMY_DATABASE_URI'] = database_connection(configuracion, basedir=basedir)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    init_db(app)
    from cotizaciones.config.db import db

    importar_modelos_alchemy()
    registrar_handlers()

    with app.app_context():
        db.create_all()

    if os.getenv('BROKER_HOST'):
        comenzar_consumidor(app)

    # Registro de blueprints
    from . import cotizaciones as api_cotizaciones
    app.register_blueprint(api_cotizaciones.bp)

    @app.route("/health")
    def health():
        return {"status": "up"}

    return app
