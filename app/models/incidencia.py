from datetime import datetime
from app.extensions import db

class IncidenciaObra(db.Model):
    __tablename__ = 'incidencias_obra'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_asiento = db.Column(db.Integer, db.ForeignKey('asientos_cuaderno.id'), nullable=False, index=True)
    tipo_incidencia = db.Column(db.String(100), nullable=False)  # 'Retraso de proveedor', 'Vicio oculto', 'Clima adverso', 'Interferencia de terceros', 'Otro'
    descripcion = db.Column(db.Text, nullable=False)
    impacto_contractual = db.Column(db.String(100), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    evidencias = db.relationship('Evidencia', backref='incidencia', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_evidencias=False):
        data = {
            'id': self.id,
            'id_asiento': self.id_asiento,
            'tipo_incidencia': self.tipo_incidencia,
            'descripcion': self.descripcion,
            'impacto_contractual': self.impacto_contractual,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
        if include_evidencias:
            data['evidencias'] = [e.to_dict() for e in self.evidencias]
        return data

    def __repr__(self):
        return f"<IncidenciaObra #{self.id} Asiento {self.id_asiento} - {self.tipo_incidencia}>"
