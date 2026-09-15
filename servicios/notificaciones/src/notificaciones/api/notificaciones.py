"""Adaptador de entrada HTTP: SOLO queries síncronas (lado Q) para clientes
y escenarios. Los comandos llegan por el broker (consumidores.py)."""
import notificaciones.seedwork.presentacion.api as api
from flask import jsonify
from notificaciones.seedwork.aplicacion.queries import ejecutar_query
from notificaciones.modulos.notificaciones.aplicacion.mapeadores import MapeadorNotificacionDTOJson
from notificaciones.modulos.notificaciones.aplicacion.queries.listar import ListarNotificaciones

bp = api.crear_blueprint('notificaciones', '/notificaciones')


@bp.route('', methods=('GET',))
def listar_usando_query():
    resultado = ejecutar_query(ListarNotificaciones())
    m = MapeadorNotificacionDTOJson()
    return jsonify([m.dto_a_externo(d) for d in resultado.resultado])
