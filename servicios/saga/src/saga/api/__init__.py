import os
import threading

from flask import Flask, jsonify

basedir = os.path.abspath(os.path.dirname(__file__))


def importar_modelos_alchemy():
    import saga.modulos.saga.infraestructura.dto  # noqa


def registrar_handlers():
    import saga.modulos.saga.aplicacion  # noqa


def comenzar_consumidor(app):
    import saga.modulos.saga.infraestructura.consumidores as c
    for objetivo in (c.suscribirse_a_comandos, c.suscribirse_a_eventos_cotizacion,
                     c.suscribirse_a_eventos_pago, c.suscribirse_a_eventos_trabajo):
        threading.Thread(target=objetivo, args=(app,), daemon=True).start()


def create_app(configuracion={}):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = "5a2c1e3f-hogar-de-los-alpes-saga"
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["TESTING"] = configuracion.get("TESTING")

    from saga.config.db import init_db, database_connection
    app.config["SQLALCHEMY_DATABASE_URI"] = database_connection(configuracion, basedir=basedir)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"timeout": 15}}
    init_db(app)
    from saga.config.db import db

    importar_modelos_alchemy()
    registrar_handlers()
    with app.app_context():
        db.create_all()

    if not configuracion.get("TESTING"):
        comenzar_consumidor(app)

    from . import sagas as api_sagas
    app.register_blueprint(api_sagas.bp)

    @app.route("/health")
    def health():
        return {"status": "up", "servicio": "saga", "persistencia": "crud + saga log"}

    return app
