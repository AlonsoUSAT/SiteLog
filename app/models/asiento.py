from datetime import datetime
from app.extensions import db

class AsientoCuaderno(db.Model):
    __tablename__ = 'asientos_cuaderno'
    __table_args__ = (
        db.UniqueConstraint('id_obra', 'numero_correlativo', name='uq_obra_correlativo'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_obra = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False, index=True)
    id_frente = db.Column(db.Integer, db.ForeignKey('frentes_obra.id'), nullable=True)
    numero_correlativo = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'Consulta', 'Notificación', 'Instrucción', 'Modificación'
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    lat_registro = db.Column(db.Float, nullable=False)
    lon_registro = db.Column(db.Float, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    estado = db.Column(db.String(50), default='Emitido', nullable=False)  # 'Emitido', 'Pendiente de Absolución', 'Absuelto', 'Observado', 'Concluido'
    codigo_qr_verificacion = db.Column(db.String(100), unique=True, nullable=True, index=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    # UUID generado por el cliente Android (operación offline) para evitar duplicados al reintentar
    uuid_operacion = db.Column(db.String(64), unique=True, nullable=True, index=True)

    # Relaciones
    usuario = db.relationship('Usuario', backref='asientos_registrados')
    respuestas = db.relationship('RespuestaAsiento', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')
    incidencias = db.relationship('IncidenciaObra', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')
    evidencias = db.relationship('Evidencia', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')
    historial = db.relationship('HistorialCambio', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_details=False):
        data = {
            'id': self.id,
            'id_obra': self.id_obra,
            'id_frente': self.id_frente,
            'frente_nombre': self.frente.nombre_sector if self.frente else None,
            'numero_correlativo': self.numero_correlativo,
            'tipo': self.tipo,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'lat_registro': self.lat_registro,
            'lon_registro': self.lon_registro,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'estado': self.estado,
            'codigo_qr_verificacion': self.codigo_qr_verificacion,
            'id_usuario': self.id_usuario,
            'usuario_nombre': self.usuario.nombre if self.usuario else None,
            'uuid_operacion': self.uuid_operacion
        }
        if include_details:
            data['respuestas'] = [r.to_dict() for r in self.respuestas]
            data['incidencias'] = [inc.to_dict() for inc in self.incidencias]
            data['evidencias'] = [e.to_dict() for e in self.evidencias]
        return data

    def __repr__(self):
        return f"<AsientoCuaderno #{self.numero_correlativo} Obra {self.id_obra} - {self.titulo}>"
