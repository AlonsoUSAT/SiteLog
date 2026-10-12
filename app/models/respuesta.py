from datetime import datetime
from app.extensions import db

class RespuestaAsiento(db.Model):
    __tablename__ = 'respuestas_asiento'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_asiento = db.Column(db.Integer, db.ForeignKey('asientos_cuaderno.id'), nullable=False, index=True)
    id_supervisor = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_respuesta = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    supervisor = db.relationship('Usuario', backref='respuestas_emitidas')

    def to_dict(self):
        return {
            'id': self.id,
            'id_asiento': self.id_asiento,
            'id_supervisor': self.id_supervisor,
            'supervisor_nombre': self.supervisor.nombre if self.supervisor else None,
            'descripcion': self.descripcion,
            'fecha_respuesta': self.fecha_respuesta.isoformat() if self.fecha_respuesta else None
        }

    def __repr__(self):
        return f"<RespuestaAsiento #{self.id} Asiento {self.id_asiento}>"
