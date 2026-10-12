from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.asiento import AsientoCuaderno
from app.models.incidencia import IncidenciaObra
from app.models.obra import Obra
from app.utils.decorators import role_required

supervision_bp = Blueprint('supervision', __name__, url_prefix='/supervision')

@supervision_bp.route('/kpis-contractuales', methods=['GET'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def kpis_contractuales():
    """
    GET /supervision/kpis-contractuales
    KPIs para panel de supervisión y monitoreo contractual:
    - Obras en ejecución
    - Consultas pendientes de absolución
    - Asientos observados
    - Incidencias técnicas abiertas
    """
    total_obras = Obra.query.count()
    obras_en_ejecucion = Obra.query.filter_by(estado='En ejecución').count()
    obras_con_observaciones = Obra.query.filter_by(estado='Con observaciones').count()

    consultas_pendientes = AsientoCuaderno.query.filter_by(
        tipo='Consulta', estado='Pendiente de Absolución'
    ).count()

    asientos_emitidos = AsientoCuaderno.query.filter_by(estado='Emitido').count()
    asientos_absueltos = AsientoCuaderno.query.filter_by(estado='Absuelto').count()
    asientos_observados = AsientoCuaderno.query.filter_by(estado='Observado').count()
    total_incidencias = IncidenciaObra.query.count()

    return jsonify({
        'success': True,
        'kpis': {
            'total_obras': total_obras,
            'obras_en_ejecucion': obras_en_ejecucion,
            'obras_con_observaciones': obras_con_observaciones,
            'consultas_pendientes': consultas_pendientes,
            'asientos_emitidos': asientos_emitidos,
            'asientos_absueltos': asientos_absueltos,
            'asientos_observados': asientos_observados,
            'total_incidencias': total_incidencias
        }
    }), 200
