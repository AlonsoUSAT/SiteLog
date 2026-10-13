from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required
from app.services.supervision_service import SupervisionService

supervision_bp = Blueprint('supervision', __name__, url_prefix='/supervision')

@supervision_bp.route('/kpis-contractuales', methods=['GET'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def kpis_contractuales():
    """
    GET /supervision/kpis-contractuales
    Capa Route: Devuelve KPIs consolidados delegando a SupervisionService.
    """
    success, error_msg, status_code, kpis = SupervisionService.obtener_kpis()

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'kpis': kpis
    }), 200
