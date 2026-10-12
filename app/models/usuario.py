from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False)  # 'Residente', 'Supervisor', 'Administrador'
    colegiatura = db.Column(db.String(50), nullable=True)
    fcm_token = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'correo': self.correo,
            'rol': self.rol,
            'colegiatura': self.colegiatura,
            'fcm_token': self.fcm_token,
            'activo': self.activo
        }

    def __repr__(self):
        return f"<Usuario {self.correo} ({self.rol})>"
