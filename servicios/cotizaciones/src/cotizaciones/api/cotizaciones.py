"""Adaptador de entrada HTTP: SOLO queries síncronas (lado Q de CQS) para
clientes y escenarios. Los comandos NO entran por aquí: llegan por el
tópico comandos-cotizacion (consumidores.py)."""
import json

import cotizaciones.seedwork.presentacion.api as api
from flask import Response, jsonify
from cotizaciones.seedwork.aplicacion.queries import ejecutar_query
from cotizaciones.modulos.cotizaciones.aplicacion.mapeadores import MapeadorCotizacionDTOJson
from cotizaciones.modulos.cotizaciones.aplicacion.queries.obtener_cotizacion import ObtenerCotizacion
from cotizaciones.modulos.cotizaciones.aplicacion.queries.historia_cotizacion import HistoriaCotizacion

bp = api.crear_blueprint('cotizaciones', '/cotizaciones')


@bp.route('/stats', methods=('GET',))
def stats():
    from cotizaciones.modulos.cotizaciones.infraestructura.fabricas import FabricaRepositorio
    from cotizaciones.modulos.cotizaciones.dominio.repositorios import RepositorioEventosCotizaciones
    repo = FabricaRepositorio().crear_objeto(RepositorioEventosCotizaciones)
    return jsonify({"eventos_en_store": repo.contar()})


@bp.route('/<id>', methods=('GET',))
def dar_cotizacion_usando_query(id):
    resultado = ejecutar_query(ObtenerCotizacion(id))
    if resultado.resultado is None:
        return Response(json.dumps({'error': 'no existe'}), status=404, mimetype='application/json')
    return jsonify(MapeadorCotizacionDTOJson().dto_a_externo(resultado.resultado))


@bp.route('/<id>/historia', methods=('GET',))
def dar_historia_usando_query(id):
    resultado = ejecutar_query(HistoriaCotizacion(id))
    if resultado.resultado is None:
        return Response(json.dumps({'error': 'no existe'}), status=404, mimetype='application/json')
    return jsonify(resultado.resultado)
