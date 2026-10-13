from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required
from app.services.supervision_service import SupervisionService

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuarios_bp.route('/residentes', methods=['GET'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def listar_residentes():
    """
    GET /usuarios/residentes
    Capa Route: Lista ingenieros residentes activos delegando a SupervisionService.
    """
    success, error_msg, status_code, residentes = SupervisionService.listar_residentes()

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'count': len(residentes),
        'residentes': residentes
    }), 200
