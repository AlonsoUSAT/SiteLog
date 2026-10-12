from app.routes.auth import auth_bp
from app.routes.obras import obras_bp
from app.routes.asientos import asientos_bp
from app.routes.incidencias import incidencias_bp
from app.routes.supervision import supervision_bp
from app.routes.usuarios import usuarios_bp

__all__ = [
    'auth_bp',
    'obras_bp',
    'asientos_bp',
    'incidencias_bp',
    'supervision_bp',
    'usuarios_bp'
]
