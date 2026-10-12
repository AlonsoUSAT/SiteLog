from datetime import datetime
from app.extensions import db

class NotificacionLog(db.Model):
    __tablename__ = 'notificaciones_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    id_asiento = db.Column(db.Integer, db.ForeignKey('asientos_cuaderno.id'), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fcm_result = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    usuario = db.relationship('Usuario', backref='notificaciones_recibidas')

    def to_dict(self):
        return {
            'id': self.id,
            'id_usuario': self.id_usuario,
            'id_asiento': self.id_asiento,
            'tipo': self.tipo,
            'mensaje': self.mensaje,
            'fcm_result': self.fcm_result,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }

    def __repr__(self):
        return f"<NotificacionLog #{self.id} Usuario {self.id_usuario} - {self.tipo}>"
