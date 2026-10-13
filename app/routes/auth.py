from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.extensions import db
from app.models.usuario import Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /auth/login
    Público: Autentica al usuario y devuelve el JWT junto con id, nombre y rol.
    """
    data = request.get_json(silent=True) or {}
    correo = data.get('correo', '').strip().lower()
    password = data.get('password', '').strip()

    if not correo or not password:
        return jsonify({
            'success': False,
            'error': 'Correo y contraseña son obligatorios'
        }), 400

    usuario = Usuario.query.filter_by(correo=correo).first()

    if not usuario or not usuario.check_password(password):
        return jsonify({
            'success': False,
            'error': 'Credenciales inválidas'
        }), 401

    if not usuario.activo:
        return jsonify({
            'success': False,
            'error': 'Usuario inactivo. Contacte al administrador.'
        }), 403

    # Generar token JWT con el id del usuario como identidad y claims con id, nombre y rol
    access_token = create_access_token(
        identity=str(usuario.id),
        additional_claims={
            'id': usuario.id,
            'nombre': usuario.nombre,
            'rol': usuario.rol,
            'correo': usuario.correo
        }
    )

    return jsonify({
        'success': True,
        'message': 'Autenticación exitosa',
        'token': access_token,
        'access_token': access_token,
        'id': usuario.id,
        'nombre': usuario.nombre,
        'rol': usuario.rol,
        'correo': usuario.correo,
        'colegiatura': usuario.colegiatura,
        'usuario': {
            'id': usuario.id,
            'nombre': usuario.nombre,
            'correo': usuario.correo,
            'rol': usuario.rol,
            'colegiatura': usuario.colegiatura
        }
    }), 200


@auth_bp.route('/fcm-token', methods=['POST'])
@jwt_required()
def update_fcm_token():
    """
    POST /auth/fcm-token
    Autenticado: Registra o actualiza el token de FCM del dispositivo.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    fcm_token = data.get('fcm_token', '').strip()

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    usuario.fcm_token = fcm_token if fcm_token else None
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Token FCM actualizado correctamente'
    }), 200
