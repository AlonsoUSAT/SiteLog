from app.extensions import db

class Obra(db.Model):
    __tablename__ = 'obras'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_contrato = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    ubicacion_lat = db.Column(db.Float, nullable=False)
    ubicacion_lon = db.Column(db.Float, nullable=False)
    radio_metros = db.Column(db.Float, default=50.0, nullable=False)
    estado = db.Column(db.String(50), default='En ejecución', nullable=False)  # 'En ejecución', 'Con observaciones', 'Concluido'
    id_residente = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    id_supervisor = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    # Relaciones
    residente = db.relationship('Usuario', foreign_keys=[id_residente], backref='obras_residente')
    supervisor = db.relationship('Usuario', foreign_keys=[id_supervisor], backref='obras_supervisor')
    frentes = db.relationship('FrenteObra', backref='obra', lazy='dynamic', cascade='all, delete-orphan')
    asientos = db.relationship('AsientoCuaderno', backref='obra', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_frentes=False):
        data = {
            'id': self.id,
            'codigo_contrato': self.codigo_contrato,
            'nombre': self.nombre,
            'ubicacion_lat': self.ubicacion_lat,
            'ubicacion_lon': self.ubicacion_lon,
            'radio_metros': self.radio_metros,
            'estado': self.estado,
            'id_residente': self.id_residente,
            'residente_nombre': self.residente.nombre if self.residente else None,
            'id_supervisor': self.id_supervisor,
            'supervisor_nombre': self.supervisor.nombre if self.supervisor else None
        }
        if include_frentes:
            data['frentes'] = [frente.to_dict() for frente in self.frentes]
        return data

    def __repr__(self):
        return f"<Obra {self.codigo_contrato} - {self.nombre}>"
