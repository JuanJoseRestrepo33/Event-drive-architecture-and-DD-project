"""Adaptador de entrada: API REST del módulo de cotizaciones.
Traduce JSON -> comando/query (CQS); sin lógica de dominio."""
import json

import cotizaciones.seedwork.presentacion.api as api
from flask import request, Response, jsonify
from cotizaciones.seedwork.aplicacion.comandos import ejecutar_commando
from cotizaciones.seedwork.aplicacion.queries import ejecutar_query
from cotizaciones.seedwork.dominio.excepciones import ExcepcionDominio
from cotizaciones.modulos.cotizaciones.aplicacion.mapeadores import MapeadorCotizacionDTOJson
from cotizaciones.modulos.cotizaciones.aplicacion.comandos.crear_cotizacion import CrearCotizacion
from cotizaciones.modulos.cotizaciones.aplicacion.comandos.aceptar_cotizacion import AceptarCotizacion
from cotizaciones.modulos.cotizaciones.aplicacion.queries.obtener_cotizacion import ObtenerCotizacion
from cotizaciones.modulos.cotizaciones.aplicacion.queries.cotizaciones_por_trabajo import CotizacionesPorTrabajo

bp = api.crear_blueprint('cotizaciones', '/cotizaciones')


@bp.route('', methods=('POST',))
def crear_cotizacion_usando_comando():
    try:
        cotizacion_dict = request.json
        map_cotizacion = MapeadorCotizacionDTOJson()
        cotizacion_dto = map_cotizacion.externo_a_dto(cotizacion_dict)

        comando = CrearCotizacion(
            id_trabajo=cotizacion_dto.id_trabajo, id_proveedor=cotizacion_dto.id_proveedor,
            monto=cotizacion_dto.monto, moneda=cotizacion_dto.moneda,
            categoria=cotizacion_dto.categoria, descripcion=cotizacion_dto.descripcion,
            vigencia_desde=cotizacion_dto.vigencia_desde,
            vigencia_hasta=cotizacion_dto.vigencia_hasta)

        id_cotizacion = ejecutar_commando(comando)
        return Response(json.dumps({'id': id_cotizacion}), status=202,
                        mimetype='application/json')
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400,
                        mimetype='application/json')


@bp.route('/<id>/aceptar', methods=('POST',))
def aceptar_cotizacion_usando_comando(id):
    try:
        estado = ejecutar_commando(AceptarCotizacion(id_cotizacion=id))
        return Response(json.dumps({'id': id, 'estado': estado}), status=202,
                        mimetype='application/json')
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400,
                        mimetype='application/json')


@bp.route('/<id>', methods=('GET',))
def dar_cotizacion_usando_query(id):
    query_resultado = ejecutar_query(ObtenerCotizacion(id))
    if query_resultado.resultado is None:
        return Response(json.dumps({'error': 'no existe'}), status=404,
                        mimetype='application/json')
    map_cotizacion = MapeadorCotizacionDTOJson()
    return jsonify(map_cotizacion.dto_a_externo(query_resultado.resultado))


@bp.route('', methods=('GET',))
def dar_cotizaciones_por_trabajo_usando_query():
    id_trabajo = request.args.get('trabajo', '')
    query_resultado = ejecutar_query(CotizacionesPorTrabajo(id_trabajo))
    map_cotizacion = MapeadorCotizacionDTOJson()
    return jsonify([map_cotizacion.dto_a_externo(c) for c in query_resultado.resultado])
