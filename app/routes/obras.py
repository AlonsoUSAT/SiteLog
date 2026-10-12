from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.obra import Obra
from app.models.asiento import AsientoCuaderno
from app.models.usuario import Usuario

obras_bp = Blueprint('obras', __name__, url_prefix='/obras')

@obras_bp.route('', methods=['GET'])
@jwt_required()
def listar_obras():
    """
    GET /obras
    Lista obras según el rol del usuario autenticado o filtros de consulta.
    """
    user_id = get_jwt_identity()
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({'success': False, 'error': 'Usuario no válido'}), 401

    query = Obra.query

    # Filtros según rol
    if usuario.rol == 'Residente':
        query = query.filter(Obra.id_residente == usuario.id)
    elif usuario.rol == 'Supervisor':
        query = query.filter(Obra.id_supervisor == usuario.id)
    # Administrador puede ver todas

    # Filtros opcionales por query param
    estado = request.args.get('estado')
    if estado:
        query = query.filter(Obra.estado == estado)

    obras = query.order_by(Obra.id.desc()).all()
    return jsonify({
        'success': True,
        'count': len(obras),
        'obras': [obra.to_dict(include_frentes=True) for obra in obras]
    }), 200


@obras_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def detalle_obra(id):
    """
    GET /obras/<id>
    Detalle general de la obra con frentes y resumen de asientos.
    """
    obra = Obra.query.get(id)
    if not obra:
        return jsonify({'success': False, 'error': 'Obra no encontrada'}), 404

    total_asientos = AsientoCuaderno.query.filter_by(id_obra=id).count()
    asientos_pendientes = AsientoCuaderno.query.filter_by(
        id_obra=id, estado='Pendiente de Absolución'
    ).count()

    data = obra.to_dict(include_frentes=True)
    data['resumen'] = {
        'total_asientos': total_asientos,
        'asientos_pendientes': asientos_pendientes
    }

    return jsonify({
        'success': True,
        'obra': data
    }), 200


@obras_bp.route('/<int:id>/asientos', methods=['GET'])
@jwt_required()
def listar_asientos_obra(id):
    """
    GET /obras/<id>/asientos
    Lista cronológica de asientos del cuaderno con filtros opcionales (tipo, estado, fechas).
    """
    obra = Obra.query.get(id)
    if not obra:
        return jsonify({'success': False, 'error': 'Obra no encontrada'}), 404

    query = AsientoCuaderno.query.filter_by(id_obra=id)

    # Filtros
    tipo = request.args.get('tipo')
    if tipo:
        query = query.filter(AsientoCuaderno.tipo == tipo)

    estado = request.args.get('estado')
    if estado:
        query = query.filter(AsientoCuaderno.estado == estado)

    fecha_inicio = request.args.get('fecha_inicio')
    if fecha_inicio:
        query = query.filter(AsientoCuaderno.fecha_registro >= fecha_inicio)

    fecha_fin = request.args.get('fecha_fin')
    if fecha_fin:
        query = query.filter(AsientoCuaderno.fecha_registro <= fecha_fin)

    asientos = query.order_by(AsientoCuaderno.numero_correlativo.asc()).all()

    return jsonify({
        'success': True,
        'id_obra': id,
        'total': len(asientos),
        'asientos': [asiento.to_dict() for asiento in asientos]
    }), 200
