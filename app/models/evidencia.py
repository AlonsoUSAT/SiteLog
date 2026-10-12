from datetime import datetime
from app.extensions import db

class Evidencia(db.Model):
    __tablename__ = 'evidencias'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_asiento = db.Column(db.Integer, db.ForeignKey('asientos_cuaderno.id'), nullable=True, index=True)
    id_incidencia = db.Column(db.Integer, db.ForeignKey('incidencias_obra.id'), nullable=True, index=True)
    ruta_archivo = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), default='IMAGEN', nullable=False)  # 'IMAGEN', 'DOCUMENTO'
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'id_asiento': self.id_asiento,
            'id_incidencia': self.id_incidencia,
            'ruta_archivo': self.ruta_archivo,
            'tipo': self.tipo,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }

    def __repr__(self):
        return f"<Evidencia #{self.id} Archivo {self.ruta_archivo}>"
