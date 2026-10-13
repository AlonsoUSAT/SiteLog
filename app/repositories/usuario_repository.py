from app.extensions import db
from app.models.usuario import Usuario

class UsuarioRepository:
    """Capa de acceso a datos para la entidad Usuario."""

    @staticmethod
    def get_by_id(user_id: int):
        return Usuario.query.get(user_id)

    @staticmethod
    def get_by_correo(correo: str):
        return Usuario.query.filter_by(correo=correo).first()

    @staticmethod
    def get_residentes_activos():
        return Usuario.query.filter_by(rol='Residente', activo=True).all()

    @staticmethod
    def update_fcm_token(user_id: int, fcm_token: str):
        usuario = Usuario.query.get(user_id)
        if usuario:
            usuario.fcm_token = fcm_token if fcm_token else None
            db.session.commit()
            return usuario
        return None
