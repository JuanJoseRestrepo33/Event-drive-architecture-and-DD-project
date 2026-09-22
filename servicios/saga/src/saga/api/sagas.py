"""Queries HTTP del orquestador: estado de las sagas y SAGA LOG (monitoreo)."""
import json

import saga.seedwork.presentacion.api as api
from flask import Response, jsonify, request
from saga.seedwork.aplicacion.queries import ejecutar_query
from saga.modulos.saga.aplicacion.queries.consultas import ObtenerSaga, ListarSagas, UltimasEntradasLog

bp = api.crear_blueprint("sagas", "/sagas")


@bp.route("", methods=("GET",))
def listar():
    return jsonify(ejecutar_query(ListarSagas()).resultado)


@bp.route("/log", methods=("GET",))
def ultimas_entradas():
    n = int(request.args.get("n", "50"))
    return jsonify(ejecutar_query(UltimasEntradasLog(n)).resultado)


@bp.route("/<ref>", methods=("GET",))
def obtener(ref):
    r = ejecutar_query(ObtenerSaga(ref)).resultado
    if r is None:
        return Response(json.dumps({"error": "no existe saga para esa referencia"}), status=404,
                        mimetype="application/json")
    return jsonify(r)


@bp.route("/<ref>/log", methods=("GET",))
def log_de_saga(ref):
    r = ejecutar_query(ObtenerSaga(ref)).resultado
    if r is None:
        return Response(json.dumps({"error": "no existe saga para esa referencia"}), status=404,
                        mimetype="application/json")
    return jsonify({"id_saga": r["id_saga"], "estado": r["estado"], "log": r["log"]})


@bp.route("/stats", methods=("GET",))
def stats():
    return jsonify(ejecutar_query(ListarSagas()).resultado["por_estado"])
