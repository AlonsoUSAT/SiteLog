from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.incidencia import IncidenciaObra
from app.utils.decorators import role_required

incidencias_bp = Blueprint('incidencias', __name__, url_prefix='/incidencias')


@incidencias_bp.route('', methods=['GET'])
@jwt_required()
def listar_incidencias():
    """
    GET /incidencias
    Lista todas las incidencias registradas, con filtro opcional por id_asiento.
    """
    try:
        id_asiento = request.args.get('id_asiento', type=int)
        query = IncidenciaObra.query

        if id_asiento is not None:
            query = query.filter_by(id_asiento=id_asiento)

        incidencias = query.order_by(IncidenciaObra.fecha_registro.desc()).all()

        return jsonify({
            'success': True,
            'count': len(incidencias),
            'incidencias': [inc.to_dict(include_evidencias=True) for inc in incidencias]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al consultar incidencias: {str(e)}'
        }), 500


@incidencias_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def detalle_incidencia(id):
    """
    GET /incidencias/<id>
    Detalle completo de una incidencia técnica con sus evidencias asociadas.
    """
    try:
        incidencia = IncidenciaObra.query.get(id)
        if not incidencia:
            return jsonify({'success': False, 'error': 'Incidencia no encontrada'}), 404

        return jsonify({
            'success': True,
            'incidencia': incidencia.to_dict(include_evidencias=True)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener detalle de la incidencia: {str(e)}'
        }), 500


@incidencias_bp.route('/<int:id>/estado', methods=['PUT'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def actualizar_estado_incidencia(id):
    """
    PUT /incidencias/<id>/estado
    Permite al supervisor actualizar o agregar una observación/impacto a la incidencia técnica.
    """
    try:
        incidencia = IncidenciaObra.query.get(id)
        if not incidencia:
            return jsonify({'success': False, 'error': 'Incidencia no encontrada'}), 404

        data = request.get_json(silent=True) or {}
        observacion = data.get('observacion', '').strip()
        impacto_actualizado = data.get('impacto_contractual')
        tipo_actualizado = data.get('tipo_incidencia')

        if not any([observacion, impacto_actualizado, tipo_actualizado]):
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar al menos un campo para actualizar: observacion, impacto_contractual o tipo_incidencia'
            }), 400

        if impacto_actualizado:
            incidencia.impacto_contractual = impacto_actualizado.strip()
        if tipo_actualizado:
            incidencia.tipo_incidencia = tipo_actualizado.strip()
        if observacion:
            incidencia.descripcion = f"{incidencia.descripcion} [Obs. Supervisor: {observacion}]"

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Incidencia actualizada correctamente',
            'incidencia': incidencia.to_dict(include_evidencias=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error al actualizar incidencia: {str(e)}'
        }), 500
