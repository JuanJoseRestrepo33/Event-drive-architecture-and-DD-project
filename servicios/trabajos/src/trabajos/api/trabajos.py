"""Adaptador de entrada HTTP: SOLO queries síncronas (lado Q) para clientes
y escenarios. Los comandos llegan por el broker (consumidores.py)."""
import trabajos.seedwork.presentacion.api as api
from flask import jsonify
from trabajos.seedwork.aplicacion.queries import ejecutar_query
from trabajos.modulos.trabajos.aplicacion.mapeadores import MapeadorAgendaDeTrabajoDTOJson
from trabajos.modulos.trabajos.aplicacion.queries.listar import ListarAgendas

bp = api.crear_blueprint('trabajos', '/trabajos')


@bp.route('', methods=('GET',))
def listar_usando_query():
    resultado = ejecutar_query(ListarAgendas())
    m = MapeadorAgendaDeTrabajoDTOJson()
    return jsonify([m.dto_a_externo(d) for d in resultado.resultado])
