from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.obra_service import ObraService

obras_bp = Blueprint('obras', __name__, url_prefix='/obras')

@obras_bp.route('', methods=['GET'])
@jwt_required()
def listar_obras():
    """
    GET /obras
    Capa Route: Delega la consulta y filtros de obras por rol a ObraService.
    """
    user_id = int(get_jwt_identity())
    estado = request.args.get('estado')
    id_residente_str = request.args.get('residente') or request.args.get('id_residente')

    id_residente = None
    if id_residente_str:
        try:
            id_residente = int(id_residente_str)
        except ValueError:
            return jsonify({'success': False, 'error': 'El parámetro residente debe ser un ID numérico'}), 400

    success, error_msg, status_code, obras = ObraService.listar_obras(
        user_id=user_id,
        estado=estado,
        id_residente=id_residente
    )

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'count': len(obras),
        'obras': obras
    }), 200


@obras_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def detalle_obra(id):
    """
    GET /obras/<id>
    Capa Route: Obtiene detalle, frentes y resumen de asientos delegando a ObraService.
    """
    user_id = int(get_jwt_identity())
    success, error_msg, status_code, data = ObraService.obtener_detalle_obra(id, user_id)

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'obra': data
    }), 200


@obras_bp.route('/<int:id>/asientos', methods=['GET'])
@jwt_required()
def listar_asientos_obra(id):
    """
    GET /obras/<id>/asientos
    Capa Route: Lista asientos cronológicos de la obra delegando filtros a ObraService.
    """
    user_id = int(get_jwt_identity())
    tipo = request.args.get('tipo')
    estado = request.args.get('estado')
    id_frente_str = request.args.get('id_frente')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    id_frente = None
    if id_frente_str:
        try:
            id_frente = int(id_frente_str)
        except ValueError:
            return jsonify({'success': False, 'error': 'id_frente debe ser un número entero'}), 400

    success, error_msg, status_code, data = ObraService.listar_asientos_obra(
        obra_id=id,
        user_id=user_id,
        tipo=tipo,
        estado=estado,
        id_frente=id_frente,
        fecha_inicio_str=fecha_inicio,
        fecha_fin_str=fecha_fin
    )

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    response = {'success': True}
    response.update(data)
    return jsonify(response), 200
