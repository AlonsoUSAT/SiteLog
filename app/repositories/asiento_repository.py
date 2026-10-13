from datetime import datetime
from app.extensions import db
from app.models.asiento import AsientoCuaderno
from app.models.respuesta import RespuestaAsiento
from app.models.historial import HistorialCambio

class AsientoRepository:
    """Capa de acceso a datos para la entidad AsientoCuaderno, respuestas e historial."""

    @staticmethod
    def get_by_id(asiento_id: int):
        return AsientoCuaderno.query.get(asiento_id)

    @staticmethod
    def get_by_qr(codigo_qr: str):
        return AsientoCuaderno.query.filter_by(codigo_qr_verificacion=codigo_qr).first()

    @staticmethod
    def get_asientos_by_obra(id_obra: int, tipo: str = None, estado: str = None, id_frente: int = None, fecha_inicio = None, fecha_fin = None):
        query = AsientoCuaderno.query.filter_by(id_obra=id_obra)

        if tipo:
            query = query.filter(AsientoCuaderno.tipo == tipo.strip())
        if estado:
            query = query.filter(AsientoCuaderno.estado == estado.strip())
        if id_frente:
            query = query.filter(AsientoCuaderno.id_frente == id_frente)
        if fecha_inicio:
            query = query.filter(AsientoCuaderno.fecha_registro >= fecha_inicio)
        if fecha_fin:
            query = query.filter(AsientoCuaderno.fecha_registro <= fecha_fin)

        return query.order_by(AsientoCuaderno.numero_correlativo.asc()).all()

    @staticmethod
    def get_siguiente_correlativo_con_bloqueo(id_obra: int):
        """Obtiene el correlativo siguiente mediante bloqueo pesimista para evitar colisiones."""
        ultimo = (
            AsientoCuaderno.query
            .filter_by(id_obra=id_obra)
            .order_by(AsientoCuaderno.numero_correlativo.desc())
            .with_for_update()
            .first()
        )
        return (ultimo.numero_correlativo + 1) if ultimo else 1

    @staticmethod
    def create_asiento(asiento: AsientoCuaderno, comentario_inicial: str = None):
        db.session.add(asiento)
        db.session.flush()

        historial = HistorialCambio(
            id_asiento=asiento.id,
            estado_anterior=None,
            estado_nuevo=asiento.estado,
            comentario=comentario_inicial or 'Registro inicial de asiento en cuaderno de obra digital',
            id_usuario=asiento.id_usuario,
            fecha=datetime.utcnow()
        )
        db.session.add(historial)
        db.session.commit()
        return asiento

    @staticmethod
    def add_respuesta(asiento: AsientoCuaderno, respuesta: RespuestaAsiento, nuevo_estado: str):
        estado_previo = asiento.estado
        db.session.add(respuesta)

        asiento.estado = nuevo_estado

        historial = HistorialCambio(
            id_asiento=asiento.id,
            estado_anterior=estado_previo,
            estado_nuevo=nuevo_estado,
            comentario=f'Absolución formal registrada por supervisor: {respuesta.descripcion[:100]}...',
            id_usuario=respuesta.id_supervisor,
            fecha=datetime.utcnow()
        )
        db.session.add(historial)
        db.session.commit()
        return respuesta

    @staticmethod
    def get_historial(id_asiento: int):
        return HistorialCambio.query.filter_by(id_asiento=id_asiento).order_by(HistorialCambio.fecha.asc()).all()
