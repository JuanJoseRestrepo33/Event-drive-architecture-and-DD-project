import os
import threading

from flask import Flask, jsonify

basedir = os.path.abspath(os.path.dirname(__file__))


def registrar_handlers():
    import pagos.modulos.pagos.aplicacion  # noqa: cablea señales *Integracion


def importar_modelos_alchemy():
    import pagos.modulos.pagos.infraestructura.dto  # noqa


def comenzar_consumidor(app):
    """Suscripciones al broker en hilos (tópico de comandos + tópicos de eventos)."""
    import pagos.modulos.pagos.infraestructura.consumidores as consumidores
    for objetivo in (consumidores.suscribirse_a_comandos,):
        threading.Thread(target=objetivo, args=(app,), daemon=True).start()


def create_app(configuracion={}):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = '5a2c1e3f-hogar-de-los-alpes-pagos'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['TESTING'] = configuracion.get('TESTING')

    from pagos.config.db import init_db, database_connection
    app.config['SQLALCHEMY_DATABASE_URI'] = database_connection(configuracion, basedir=basedir)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 15}}
    init_db(app)
    from pagos.config.db import db

    importar_modelos_alchemy()
    registrar_handlers()
    with app.app_context():
        db.create_all()

    if not configuracion.get('TESTING'):
        comenzar_consumidor(app)

    from . import pagos as api_modulo
    app.register_blueprint(api_modulo.bp)

    @app.route("/health")
    def health():
        return {"status": "up", "servicio": "pagos", "persistencia": "crud"}

    @app.route("/stats")
    def stats():
        from pagos.modulos.pagos.infraestructura.fabricas import FabricaRepositorio
        from pagos.modulos.pagos.dominio.repositorios import RepositorioReservas
        return jsonify({"reservas": FabricaRepositorio().crear_objeto(RepositorioReservas).contar()})

    return app
