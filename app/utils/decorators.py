from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.usuario import Usuario


def get_current_user():
    """Devuelve la instancia de Usuario autenticado en la petición actual."""
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    return Usuario.query.get(int(user_id)) if user_id else None


def role_required(allowed_roles):
    """
    Decorador/Middleware para validar el token JWT y verificar que el usuario
    autenticado posea uno de los roles autorizados.
    Acepta un string ('Residente') o una lista (['Supervisor', 'Administrador']).
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            usuario = Usuario.query.get(int(user_id)) if user_id else None

            if not usuario or not usuario.activo:
                return jsonify({
                    'success': False,
                    'error': 'Usuario no encontrado o inactivo'
                }), 401

            if usuario.rol not in allowed_roles:
                return jsonify({
                    'success': False,
                    'error': f'Acceso denegado. Se requiere rol: {", ".join(allowed_roles)} (Tu rol actual: {usuario.rol})'
                }), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
