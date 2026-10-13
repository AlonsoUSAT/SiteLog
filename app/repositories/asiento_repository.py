from datetime import datetime
from app.extensions import db
from app.models.asiento import AsientoCuaderno
from app.models.obra import Obra
from app.models.respuesta import RespuestaAsiento
from app.models.historial import HistorialCambio

class AsientoRepository:
    """Capa de acceso a datos para la entidad AsientoCuaderno, respuestas e historial."""

    @staticmethod
    def get_by_id(asiento_id: int):
        return AsientoCuaderno.query.get(asiento_id)

    @staticmethod
    def get_by_id_with_lock(asiento_id: int):
        return AsientoCuaderno.query.filter_by(id=asiento_id).with_for_update().first()

    @staticmethod
    def get_by_qr(codigo_qr: str):
        return AsientoCuaderno.query.filter_by(codigo_qr_verificacion=codigo_qr.strip()).first()

    @staticmethod
    def get_by_uuid(uuid_operacion: str):
        if not uuid_operacion:
            return None
        return AsientoCuaderno.query.filter_by(uuid_operacion=uuid_operacion.strip()).first()

    @staticmethod
    def get_asientos_by_obra(id_obra: int, tipo: str = None, estado: str = None, id_frente: int = None, fecha_inicio = None, fecha_fin = None):
        query = AsientoCuaderno.query.filter_by(id_obra=id_obra)

        if tipo:
            query = query.filter(AsientoCuaderno.tipo == tipo.strip())

        # Soporte para estados oficiales y para el filtro calculado 'Pendiente de absolución'
        if estado:
            estado_limpio = estado.strip()
            if estado_limpio.lower() in ['pendiente de absolución', 'pendiente_absolucion']:
                # Consulta en estado EMITIDO y sin respuesta
                query = query.filter(
                    AsientoCuaderno.tipo == 'Consulta',
                    AsientoCuaderno.estado == 'EMITIDO',
                    ~AsientoCuaderno.respuestas.any()
                )
            else:
                query = query.filter(AsientoCuaderno.estado == estado_limpio)

        if id_frente:
            query = query.filter(AsientoCuaderno.id_frente == id_frente)
        if fecha_inicio:
            query = query.filter(AsientoCuaderno.fecha_registro >= fecha_inicio)
        if fecha_fin:
            query = query.filter(AsientoCuaderno.fecha_registro <= fecha_fin)

        return query.order_by(AsientoCuaderno.numero_correlativo.asc()).all()

    @staticmethod
    def get_siguiente_correlativo_con_bloqueo(id_obra: int):
        """Bloquea la fila de la obra para serializar el cálculo del correlativo y evitar colisiones concurrentes."""
        obra = Obra.query.filter_by(id=id_obra).with_for_update().first()
        if not obra:
            return None, "Obra no encontrada"

        ultimo = (
            AsientoCuaderno.query
            .filter_by(id_obra=id_obra)
            .order_by(AsientoCuaderno.numero_correlativo.desc())
            .first()
        )
        siguiente = (ultimo.numero_correlativo + 1) if ultimo else 1
        return siguiente, obra

    @staticmethod
    def create_asiento(asiento: AsientoCuaderno, comentario_inicial: str = None):
        db.session.add(asiento)
        db.session.flush()

        historial = HistorialCambio(
            id_asiento=asiento.id,
            estado_anterior=None,
            estado_nuevo=asiento.estado,
            comentario=comentario_inicial or 'Emisión oficial del asiento con correlativo y hash SHA-256',
            id_usuario=asiento.id_usuario,
            fecha=datetime.utcnow()
        )
        db.session.add(historial)
        db.session.commit()
        return asiento

    @staticmethod
    def cambiar_estado(asiento: AsientoCuaderno, nuevo_estado: str, usuario_id: int, comentario: str = None):
        """Aplica una transición de estado y registra en historial_cambios."""
        estado_previo = asiento.estado
        asiento.estado = nuevo_estado

        historial = HistorialCambio(
            id_asiento=asiento.id,
            estado_anterior=estado_previo,
            estado_nuevo=nuevo_estado,
            comentario=comentario or f'Transición de estado: {estado_previo} -> {nuevo_estado}',
            id_usuario=usuario_id,
            fecha=datetime.utcnow()
        )
        db.session.add(historial)
        db.session.commit()
        return asiento

    @staticmethod
    def add_respuesta(asiento: AsientoCuaderno, respuesta: RespuestaAsiento, nuevo_estado: str = 'ABSUELTO'):
        estado_previo = asiento.estado
        db.session.add(respuesta)

        asiento.estado = nuevo_estado

        historial = HistorialCambio(
            id_asiento=asiento.id,
            estado_anterior=estado_previo,
            estado_nuevo=nuevo_estado,
            comentario=f'Respuesta formal del supervisor: {respuesta.descripcion}',
            id_usuario=respuesta.id_supervisor,
            fecha=datetime.utcnow()
        )
        db.session.add(historial)
        db.session.commit()
        return respuesta

    @staticmethod
    def get_historial(id_asiento: int):
        return HistorialCambio.query.filter_by(id_asiento=id_asiento).order_by(
            HistorialCambio.fecha.asc(), HistorialCambio.id.asc()
        ).all()
