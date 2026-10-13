import hashlib
from datetime import datetime
from app.extensions import db

ESTADOS_OFICIALES = ['PENDIENTE_SINCRONIZACION', 'EMITIDO', 'OBSERVADO', 'ABSUELTO', 'CONCLUIDO']

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
    accuracy_registro = db.Column(db.Float, nullable=True)  # Precisión del GPS en metros
    fecha_registro = db.Column(db.DateTime, default=lambda: datetime.utcnow().replace(microsecond=0), nullable=False)
    # Ciclo de vida oficial de 5 estados (Sección 4.1 de la Versión 2)
    estado = db.Column(db.String(50), default='EMITIDO', nullable=False)
    hash_contenido = db.Column(db.String(64), nullable=True)  # SHA-256 inmutable de autenticidad
    codigo_qr_verificacion = db.Column(db.String(100), unique=True, nullable=True, index=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    # UUID generado en Android (operación offline) para idempotencia
    uuid_operacion = db.Column(db.String(64), unique=True, nullable=True, index=True)

    # Relaciones
    usuario = db.relationship('Usuario', backref='asientos_registrados')
    respuestas = db.relationship('RespuestaAsiento', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')
    incidencias = db.relationship('IncidenciaObra', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')
    evidencias = db.relationship('Evidencia', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')
    historial = db.relationship('HistorialCambio', backref='asiento', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def calcular_hash(id_obra, numero_correlativo, tipo, titulo, descripcion, lat, lon, fecha, id_usuario) -> str:
        """
        Calcula el hash SHA-256 del contenido sustantivo definitivo del asiento (Sección 4.2).
        Garantiza inalterabilidad frente a modificaciones directas no autorizadas en base de datos.
        """
        fecha_str = fecha.strftime('%Y-%m-%d %H:%M:%S') if isinstance(fecha, datetime) else str(fecha)[:19]
        canonical = (
            f"{id_obra}|{numero_correlativo}|{tipo.strip()}|{titulo.strip()}|{descripcion.strip()}|"
            f"{float(lat):.6f}|{float(lon):.6f}|{fecha_str}|{id_usuario}"
        )
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def verificar_integridad(self) -> bool:
        """Recalcula el hash sobre el contenido actual y lo contrasta contra hash_contenido."""
        if not self.hash_contenido:
            return False
        hash_actual = self.calcular_hash(
            self.id_obra,
            self.numero_correlativo,
            self.tipo,
            self.titulo,
            self.descripcion,
            self.lat_registro,
            self.lon_registro,
            self.fecha_registro,
            self.id_usuario
        )
        return hash_actual == self.hash_contenido

    def to_dict(self, include_details=False):
        # Filtro calculado de interfaz (Nota sección 4.1): Consulta en EMITIDO sin respuesta
        es_pendiente_absolucion = (
            self.tipo == 'Consulta' and 
            self.estado == 'EMITIDO' and 
            self.respuestas.count() == 0
        )

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
            'accuracy_registro': self.accuracy_registro,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'estado': self.estado,
            'pendiente_absolucion': es_pendiente_absolucion,
            'hash_contenido': self.hash_contenido,
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
        return f"<AsientoCuaderno #{self.numero_correlativo} Obra {self.id_obra} [{self.estado}] - {self.titulo}>"
