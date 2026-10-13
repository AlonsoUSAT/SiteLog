from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /auth/login
    Capa Route: Recibe credenciales y delega la autenticación y generación de JWT a AuthService.
    """
    data = request.get_json(silent=True) or {}
    correo = data.get('correo', '')
    password = data.get('password', '')

    success, message, status_code, result_data = AuthService.login(correo, password)

    if not success:
        return jsonify({'success': False, 'error': message}), status_code

    response = {
        'success': True,
        'message': message
    }
    response.update(result_data)
    return jsonify(response), status_code


@auth_bp.route('/fcm-token', methods=['POST'])
@jwt_required()
def update_fcm_token():
    """
    POST /auth/fcm-token
    Capa Route: Registra o actualiza el token FCM delegando a AuthService.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    fcm_token = data.get('fcm_token', '')

    success, message, status_code = AuthService.actualizar_fcm_token(user_id, fcm_token)

    if not success:
        return jsonify({'success': False, 'error': message}), status_code

    return jsonify({'success': True, 'message': message}), status_code
