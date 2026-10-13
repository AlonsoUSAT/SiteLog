from flask_jwt_extended import create_access_token
from app.repositories.usuario_repository import UsuarioRepository

class AuthService:
    """Capa de lógica de negocio para autenticación y gestión de sesiones."""

    @staticmethod
    def login(correo: str, password: str):
        if not correo or not password:
            return False, "Correo y contraseña son obligatorios", 400, None

        correo_limpio = correo.strip().lower()
        usuario = UsuarioRepository.get_by_correo(correo_limpio)

        if not usuario or not usuario.check_password(password.strip()):
            return False, "Credenciales inválidas", 401, None

        if not usuario.activo:
            return False, "Usuario inactivo. Contacte al administrador.", 403, None

        # Generar token JWT con identidad y claims de rol
        access_token = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                'id': usuario.id,
                'nombre': usuario.nombre,
                'rol': usuario.rol,
                'correo': usuario.correo
            }
        )

        user_payload = {
            'id': usuario.id,
            'nombre': usuario.nombre,
            'correo': usuario.correo,
            'rol': usuario.rol,
            'colegiatura': usuario.colegiatura,
            'token': access_token
        }

        response_data = {
            'token': access_token,
            'access_token': access_token,
            'id': usuario.id,
            'nombre': usuario.nombre,
            'rol': usuario.rol,
            'correo': usuario.correo,
            'colegiatura': usuario.colegiatura,
            'data': user_payload,
            'usuario': user_payload
        }

        return True, "Autenticación exitosa", 200, response_data

    @staticmethod
    def actualizar_fcm_token(user_id: int, fcm_token: str):
        usuario = UsuarioRepository.get_by_id(user_id)
        if not usuario:
            return False, "Usuario no encontrado", 404

        UsuarioRepository.update_fcm_token(user_id, fcm_token.strip() if fcm_token else None)
        return True, "Token FCM actualizado correctamente", 200
