import uuid
from datetime import datetime
from app.extensions import db
from app.models.asiento import AsientoCuaderno
from app.models.respuesta import RespuestaAsiento
from app.repositories.asiento_repository import AsientoRepository
from app.repositories.obra_repository import ObraRepository

class AsientoService:
    """Capa de lógica de negocio para asientos, generación de token QR, respuestas y trazabilidad."""

    @staticmethod
    def registrar_asiento(user_id: int, data: dict):
        id_obra = data.get('id_obra')
        tipo = data.get('tipo', '').strip()
        titulo = data.get('titulo', '').strip()
        descripcion = data.get('descripcion', '').strip()
        lat_registro = data.get('lat_registro')
        lon_registro = data.get('lon_registro')
        id_frente = data.get('id_frente')

        if not all([id_obra, tipo, titulo, descripcion, lat_registro is not None, lon_registro is not None]):
            return False, "Faltan campos obligatorios: id_obra, tipo, titulo, descripcion, lat_registro, lon_registro", 400, None

        obra = ObraRepository.get_by_id(id_obra)
        if not obra:
            return False, "Obra no encontrada", 404, None

        try:
            siguiente_correlativo = AsientoRepository.get_siguiente_correlativo_con_bloqueo(id_obra)
            codigo_qr = f"SITELOG-OBRA{id_obra}-AS{siguiente_correlativo}-{uuid.uuid4().hex[:12].upper()}"

            nuevo_asiento = AsientoCuaderno(
                id_obra=id_obra,
                id_frente=id_frente,
                numero_correlativo=siguiente_correlativo,
                tipo=tipo,
                titulo=titulo,
                descripcion=descripcion,
                lat_registro=float(lat_registro),
                lon_registro=float(lon_registro),
                fecha_registro=datetime.utcnow(),
                estado='Pendiente de Absolución' if tipo == 'Consulta' else 'Emitido',
                codigo_qr_verificacion=codigo_qr,
                id_usuario=user_id
            )

            asiento_creado = AsientoRepository.create_asiento(nuevo_asiento)
            return True, "Asiento registrado exitosamente", 201, asiento_creado.to_dict(include_details=True)

        except Exception as e:
            db.session.rollback()
            return False, f"Error al registrar asiento: {str(e)}", 500, None

    @staticmethod
    def obtener_detalle(asiento_id: int):
        asiento = AsientoRepository.get_by_id(asiento_id)
        if not asiento:
            return False, "Asiento no encontrado", 404, None
        return True, None, 200, asiento.to_dict(include_details=True)

    @staticmethod
    def responder_asiento(asiento_id: int, user_id: int, descripcion: str, nuevo_estado: str = 'Absuelto'):
        asiento = AsientoRepository.get_by_id(asiento_id)
        if not asiento:
            return False, "Asiento no encontrado", 404, None

        if not descripcion or not descripcion.strip():
            return False, "La descripción de la absolución es obligatoria", 400, None

        try:
            respuesta = RespuestaAsiento(
                id_asiento=asiento.id,
                id_supervisor=user_id,
                descripcion=descripcion.strip(),
                fecha_respuesta=datetime.utcnow()
            )
            AsientoRepository.add_respuesta(asiento, respuesta, nuevo_estado.strip() if nuevo_estado else 'Absuelto')
            return True, "Absolución registrada exitosamente", 200, asiento.to_dict(include_details=True)

        except Exception as e:
            db.session.rollback()
            return False, f"Error al procesar respuesta: {str(e)}", 500, None

    @staticmethod
    def verificar_qr(codigo_qr: str):
        asiento = AsientoRepository.get_by_qr(codigo_qr)
        if not asiento:
            return False, "Código QR no reconocido o no registrado en el Cuaderno de Obra oficial", 404, None

        data = {
            'valido': True,
            'mensaje': 'Documento digital oficial certificado e inalterable',
            'asiento': asiento.to_dict(include_details=True),
            'verificado_en': datetime.utcnow().isoformat()
        }
        return True, None, 200, data

    @staticmethod
    def obtener_historial(asiento_id: int):
        asiento = AsientoRepository.get_by_id(asiento_id)
        if not asiento:
            return False, "Asiento no encontrado", 404, None

        historial = AsientoRepository.get_historial(asiento_id)
        return True, None, 200, [h.to_dict() for h in historial]
