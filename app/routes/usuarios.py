from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.usuario import Usuario
from app.utils.decorators import role_required

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuarios_bp.route('/residentes', methods=['GET'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def listar_residentes():
    """
    GET /usuarios/residentes
    Lista profesionales residentes de obra activos para asignación a contratos.
    """
    residentes = Usuario.query.filter_by(rol='Residente', activo=True).all()
    return jsonify({
        'success': True,
        'count': len(residentes),
        'residentes': [r.to_dict() for r in residentes]
    }), 200
