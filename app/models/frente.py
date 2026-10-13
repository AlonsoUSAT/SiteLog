from app.extensions import db

class FrenteObra(db.Model):
    __tablename__ = 'frentes_obra'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_obra = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False, index=True)
    nombre_sector = db.Column(db.String(100), nullable=False)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    radio_metros = db.Column(db.Float, default=50.0, nullable=False)

    asientos = db.relationship('AsientoCuaderno', backref='frente', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'id_obra': self.id_obra,
            'nombre_sector': self.nombre_sector,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'radio_metros': self.radio_metros
        }

    def __repr__(self):
        return f"<FrenteObra {self.nombre_sector} (Obra {self.id_obra})>"
