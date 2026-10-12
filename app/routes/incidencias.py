from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.incidencia import IncidenciaObra
from app.utils.decorators import role_required

incidencias_bp = Blueprint('incidencias', __name__, url_prefix='/incidencias')

@incidencias_bp.route('/<int:id>/estado', methods=['PUT'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def actualizar_estado_incidencia(id):
    """
    PUT /incidencias/<id>/estado
    Permite al supervisor actualizar o agregar una observación a la incidencia técnica.
    """
    incidencia = IncidenciaObra.query.get(id)
    if not incidencia:
        return jsonify({'success': False, 'error': 'Incidencia no encontrada'}), 404

    data = request.get_json(silent=True) or {}
    observacion = data.get('observacion', '').strip()
    impacto_actualizado = data.get('impacto_contractual')

    if impacto_actualizado:
        incidencia.impacto_contractual = impacto_actualizado
    if observacion:
        incidencia.descripcion = f"{incidencia.descripcion} [Obs. Supervisor: {observacion}]"

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Incidencia actualizada correctamente',
        'incidencia': incidencia.to_dict(include_evidencias=True)
    }), 200
