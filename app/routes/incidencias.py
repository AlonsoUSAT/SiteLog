from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required, get_current_user
from app.services.incidencia_service import IncidenciaService

incidencias_bp = Blueprint('incidencias', __name__, url_prefix='/incidencias')

@incidencias_bp.route('', methods=['GET'])
@jwt_required()
def listar_incidencias():
    """
    GET /incidencias
    Capa Route: Lista incidencias con filtro opcional por id_asiento delegando a IncidenciaService.
    """
    id_asiento = request.args.get('id_asiento', type=int)
    success, error_msg, status_code, incidencias = IncidenciaService.listar(id_asiento=id_asiento)

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'count': len(incidencias),
        'incidencias': incidencias
    }), 200


@incidencias_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def detalle_incidencia(id):
    """
    GET /incidencias/<id>
    Capa Route: Detalle completo de incidencia con evidencias delegando a IncidenciaService.
    """
    success, error_msg, status_code, incidencia = IncidenciaService.obtener_detalle(id)

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'incidencia': incidencia
    }), 200


@incidencias_bp.route('/<int:id>/estado', methods=['PUT'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def actualizar_estado_incidencia(id):
    """
    PUT /incidencias/<id>/estado
    Capa Route: Actualización de estado y observaciones de supervisión delegando a IncidenciaService.
    """
    data = request.get_json(silent=True) or {}
    observacion = data.get('observacion', '')
    impacto = data.get('impacto_contractual')
    tipo = data.get('tipo_incidencia')

    success, message, status_code, inc_data = IncidenciaService.actualizar_estado(
        incidencia_id=id,
        observacion=observacion,
        impacto=impacto,
        tipo=tipo
    )

    if not success:
        return jsonify({'success': False, 'error': message}), status_code

    return jsonify({
        'success': True,
        'message': message,
        'incidencia': inc_data
    }), status_code


@incidencias_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required(['Residente', 'Supervisor', 'Administrador'])
def eliminar_incidencia(id):
    """
    DELETE /incidencias/<id>
    Capa Route: Elimina una incidencia preliminar delegando a IncidenciaService.
    Valida permisos y restringe eliminación si el asiento ya se encuentra CONCLUIDO o ABSUELTO (409).
    """
    usuario = get_current_user()
    success, message, status_code, data = IncidenciaService.eliminar(id, usuario)

    if not success:
        return jsonify({'success': False, 'error': message}), status_code

    return jsonify({
        'success': True,
        'message': message,
        'data': data
    }), status_code

