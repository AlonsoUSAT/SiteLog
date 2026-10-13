from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.obra import Obra
from app.models.asiento import AsientoCuaderno
from app.models.incidencia import IncidenciaObra
from app.models.usuario import Usuario

obras_bp = Blueprint('obras', __name__, url_prefix='/obras')


@obras_bp.route('', methods=['GET'])
@jwt_required()
def listar_obras():
    """
    GET /obras
    Lista las obras según el rol del usuario autenticado y filtros opcionales.
    Filtros soportados en query params:
      - estado: 'En ejecución', 'Con observaciones', 'Concluido'
      - residente: ID del residente (solo para Administrador / Supervisor)
    """
    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({'success': False, 'error': 'Usuario no válido o sesión expirada'}), 401

    query = Obra.query

    # 1. Filtro estricto por rol
    if usuario.rol == 'Residente':
        query = query.filter(Obra.id_residente == usuario.id)
    elif usuario.rol == 'Supervisor':
        query = query.filter(Obra.id_supervisor == usuario.id)
    # Administrador tiene acceso a todas las obras

    # 2. Filtro opcional por estado
    estado = request.args.get('estado')
    if estado:
        query = query.filter(Obra.estado == estado.strip())

    # 3. Filtro opcional por residente (para Administrador o Supervisor)
    id_residente = request.args.get('residente') or request.args.get('id_residente')
    if id_residente and usuario.rol == 'Administrador':
        try:
            query = query.filter(Obra.id_residente == int(id_residente))
        except ValueError:
            return jsonify({'success': False, 'error': 'El parámetro residente debe ser un ID numérico'}), 400

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
    Detalle general de la obra con sus frentes/hitos y resumen métrico de asientos e incidencias.
    """
    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({'success': False, 'error': 'Usuario no válido'}), 401

    obra = Obra.query.get(id)
    if not obra:
        return jsonify({'success': False, 'error': f'Obra con ID {id} no encontrada'}), 404

    # Validación de acceso por rol
    if usuario.rol == 'Residente' and obra.id_residente != usuario.id:
        return jsonify({
            'success': False,
            'error': 'No tienes autorización para acceder a esta obra'
        }), 403

    if usuario.rol == 'Supervisor' and obra.id_supervisor != usuario.id:
        return jsonify({
            'success': False,
            'error': 'No estás asignado como supervisor de esta obra'
        }), 403

    # Resumen métrico contractual de asientos
    total_asientos = AsientoCuaderno.query.filter_by(id_obra=id).count()
    asientos_emitidos = AsientoCuaderno.query.filter_by(id_obra=id, estado='Emitido').count()
    asientos_pendientes = AsientoCuaderno.query.filter_by(id_obra=id, estado='Pendiente de Absolución').count()
    asientos_absueltos = AsientoCuaderno.query.filter_by(id_obra=id, estado='Absuelto').count()
    asientos_observados = AsientoCuaderno.query.filter_by(id_obra=id, estado='Observado').count()
    asientos_concluidos = AsientoCuaderno.query.filter_by(id_obra=id, estado='Concluido').count()

    # Total de incidencias técnicas en los asientos de esta obra
    total_incidencias = (
        IncidenciaObra.query
        .join(AsientoCuaderno, IncidenciaObra.id_asiento == AsientoCuaderno.id)
        .filter(AsientoCuaderno.id_obra == id)
        .count()
    )

    data = obra.to_dict(include_frentes=True)
    data['resumen'] = {
        'total_asientos': total_asientos,
        'asientos_emitidos': asientos_emitidos,
        'asientos_pendientes': asientos_pendientes,
        'asientos_absueltos': asientos_absueltos,
        'asientos_observados': asientos_observados,
        'asientos_concluidos': asientos_concluidos,
        'total_incidencias': total_incidencias
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
    Lista cronológica de los asientos del Cuaderno de Obra.
    Filtros soportados en query params:
      - tipo: 'Consulta', 'Notificación', 'Instrucción', 'Modificación'
      - estado: 'Emitido', 'Pendiente de Absolución', 'Absuelto', 'Observado', 'Concluido'
      - id_frente: ID del frente de obra
      - fecha_inicio: 'YYYY-MM-DD'
      - fecha_fin: 'YYYY-MM-DD'
    """
    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({'success': False, 'error': 'Usuario no válido'}), 401

    obra = Obra.query.get(id)
    if not obra:
        return jsonify({'success': False, 'error': f'Obra con ID {id} no encontrada'}), 404

    # Validación de acceso por rol
    if usuario.rol == 'Residente' and obra.id_residente != usuario.id:
        return jsonify({
            'success': False,
            'error': 'No tienes autorización para consultar asientos de esta obra'
        }), 403

    if usuario.rol == 'Supervisor' and obra.id_supervisor != usuario.id:
        return jsonify({
            'success': False,
            'error': 'No estás asignado a esta obra'
        }), 403

    query = AsientoCuaderno.query.filter_by(id_obra=id)

    # Filtro por tipo de asiento
    tipo = request.args.get('tipo')
    if tipo:
        query = query.filter(AsientoCuaderno.tipo == tipo.strip())

    # Filtro por estado
    estado = request.args.get('estado')
    if estado:
        query = query.filter(AsientoCuaderno.estado == estado.strip())

    # Filtro por frente de obra
    id_frente = request.args.get('id_frente')
    if id_frente:
        try:
            query = query.filter(AsientoCuaderno.id_frente == int(id_frente))
        except ValueError:
            return jsonify({'success': False, 'error': 'id_frente debe ser un número entero'}), 400

    # Filtro por rango de fechas
    fecha_inicio_str = request.args.get('fecha_inicio')
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str.strip()[:10], '%Y-%m-%d')
            query = query.filter(AsientoCuaderno.fecha_registro >= fecha_inicio)
        except ValueError:
            return jsonify({'success': False, 'error': 'Formato de fecha_inicio inválido (use YYYY-MM-DD)'}), 400

    fecha_fin_str = request.args.get('fecha_fin')
    if fecha_fin_str:
        try:
            # Fin del día: 23:59:59
            fecha_fin = datetime.strptime(fecha_fin_str.strip()[:10] + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(AsientoCuaderno.fecha_registro <= fecha_fin)
        except ValueError:
            return jsonify({'success': False, 'error': 'Formato de fecha_fin inválido (use YYYY-MM-DD)'}), 400

    # Orden cronológico oficial del cuaderno de obra (por número correlativo ascendente)
    asientos = query.order_by(AsientoCuaderno.numero_correlativo.asc()).all()

    return jsonify({
        'success': True,
        'id_obra': id,
        'obra_nombre': obra.nombre,
        'total': len(asientos),
        'asientos': [asiento.to_dict() for asiento in asientos]
    }), 200
