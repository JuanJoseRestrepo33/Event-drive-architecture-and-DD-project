"""Adaptador de entrada HTTP: SOLO queries síncronas (lado Q) para clientes
y escenarios. Los comandos llegan por el broker (consumidores.py)."""
import pagos.seedwork.presentacion.api as api
from flask import jsonify
from pagos.seedwork.aplicacion.queries import ejecutar_query
from pagos.modulos.pagos.aplicacion.mapeadores import MapeadorReservaDePagoDTOJson
from pagos.modulos.pagos.aplicacion.queries.listar import ListarReservas

bp = api.crear_blueprint('pagos', '/reservas')


@bp.route('', methods=('GET',))
def listar_usando_query():
    resultado = ejecutar_query(ListarReservas())
    m = MapeadorReservaDePagoDTOJson()
    return jsonify([m.dto_a_externo(d) for d in resultado.resultado])
