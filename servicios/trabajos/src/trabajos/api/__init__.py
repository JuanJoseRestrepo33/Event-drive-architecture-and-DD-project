import os
import threading

from flask import Flask, jsonify

basedir = os.path.abspath(os.path.dirname(__file__))


def registrar_handlers():
    import trabajos.modulos.trabajos.aplicacion  # noqa: cablea señales *Integracion


def importar_modelos_alchemy():
    import trabajos.modulos.trabajos.infraestructura.dto  # noqa


def comenzar_consumidor(app):
    """Suscripciones al broker en hilos (tópico de comandos + tópicos de eventos)."""
    import trabajos.modulos.trabajos.infraestructura.consumidores as consumidores
    for objetivo in (consumidores.suscribirse_a_comandos,):
        threading.Thread(target=objetivo, args=(app,), daemon=True).start()


def create_app(configuracion={}):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = '5a2c1e3f-hogar-de-los-alpes-trabajos'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['TESTING'] = configuracion.get('TESTING')

    from trabajos.config.db import init_db, database_connection
    app.config['SQLALCHEMY_DATABASE_URI'] = database_connection(configuracion, basedir=basedir)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 15}}
    init_db(app)
    from trabajos.config.db import db

    importar_modelos_alchemy()
    registrar_handlers()
    with app.app_context():
        db.create_all()

    if not configuracion.get('TESTING'):
        comenzar_consumidor(app)

    from . import trabajos as api_modulo
    app.register_blueprint(api_modulo.bp)

    @app.route("/health")
    def health():
        return {"status": "up", "servicio": "trabajos", "persistencia": "crud"}

    @app.route("/stats")
    def stats():
        from trabajos.modulos.trabajos.infraestructura.fabricas import FabricaRepositorio
        from trabajos.modulos.trabajos.dominio.repositorios import RepositorioAgendas
        return jsonify({"trabajos_agendados": FabricaRepositorio().crear_objeto(RepositorioAgendas).contar()})

    return app
