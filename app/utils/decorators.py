from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.usuario import Usuario

def role_required(allowed_roles):
    """
    Decorador para verificar que el usuario autenticado posea uno de los roles autorizados.
    Uso:
        @jwt_required()
        @role_required(['Supervisor', 'Administrador'])
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            usuario = Usuario.query.get(user_id)
            
            if not usuario or not usuario.activo:
                return jsonify({
                    'success': False,
                    'error': 'Usuario no encontrado o inactivo'
                }), 401

            if usuario.rol not in allowed_roles:
                return jsonify({
                    'success': False,
                    'error': f'Acceso denegado. Se requiere uno de los siguientes roles: {", ".join(allowed_roles)}'
                }), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
