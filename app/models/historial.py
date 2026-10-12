from datetime import datetime
from app.extensions import db

class HistorialCambio(db.Model):
    __tablename__ = 'historial_cambios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_asiento = db.Column(db.Integer, db.ForeignKey('asientos_cuaderno.id'), nullable=False, index=True)
    estado_anterior = db.Column(db.String(50), nullable=True)
    estado_nuevo = db.Column(db.String(50), nullable=False)
    comentario = db.Column(db.Text, nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    usuario = db.relationship('Usuario', backref='historial_acciones')

    def to_dict(self):
        return {
            'id': self.id,
            'id_asiento': self.id_asiento,
            'estado_anterior': self.estado_anterior,
            'estado_nuevo': self.estado_nuevo,
            'comentario': self.comentario,
            'id_usuario': self.id_usuario,
            'usuario_nombre': self.usuario.nombre if self.usuario else None,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }

    def __repr__(self):
        return f"<HistorialCambio #{self.id} Asiento {self.id_asiento}: {self.estado_anterior} -> {self.estado_nuevo}>"
