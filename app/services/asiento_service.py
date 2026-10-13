import math
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.asiento import AsientoCuaderno
from app.models.frente import FrenteObra
from app.models.respuesta import RespuestaAsiento
from app.repositories.asiento_repository import AsientoRepository
from app.repositories.obra_repository import ObraRepository

TIPOS_VALIDOS = ['Consulta', 'Notificación', 'Instrucción', 'Modificación']
ESTADOS_RESPUESTA = ['Absuelto', 'Observado', 'Concluido']


def distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia geodésica mediante la fórmula de Haversine en metros."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def tiene_acceso_a_obra(usuario, obra) -> bool:
    """Regla de autorización: Administrador ve todo; Residente y Supervisor solo sus asignadas."""
    if not usuario or not obra:
        return False
    if usuario.rol == 'Administrador':
        return True
    if usuario.rol == 'Residente':
        return obra.id_residente == usuario.id
    if usuario.rol == 'Supervisor':
        return obra.id_supervisor == usuario.id
    return False


class AsientoService:
    """Capa de lógica de negocio para asientos, proximidad GPS, idempotencia offline y QR."""

    @staticmethod
    def registrar_asiento(usuario, data: dict):
        id_obra = data.get('id_obra')
        tipo = str(data.get('tipo') or '').strip()
        titulo = str(data.get('titulo') or '').strip()
        descripcion = str(data.get('descripcion') or '').strip()
        lat_registro = data.get('lat_registro')
        lon_registro = data.get('lon_registro')
        id_frente = data.get('id_frente')
        uuid_operacion = str(data.get('uuid_operacion') or '').strip() or None

        if not all([id_obra, tipo, titulo, descripcion]) or lat_registro is None or lon_registro is None:
            return False, "Faltan campos obligatorios: id_obra, tipo, titulo, descripcion, lat_registro, lon_registro", 400, None

        if tipo not in TIPOS_VALIDOS:
            return False, f"Tipo inválido. Valores permitidos: {', '.join(TIPOS_VALIDOS)}", 400, None

        if len(titulo) > 150:
            return False, "El título no puede superar los 150 caracteres", 400, None

        try:
            lat_registro = float(lat_registro)
            lon_registro = float(lon_registro)
        except (TypeError, ValueError):
            return False, "lat_registro y lon_registro deben ser numéricos", 400, None

        if not (-90 <= lat_registro <= 90 and -180 <= lon_registro <= 180):
            return False, "Coordenadas fuera de rango válido", 400, None

        # 1. Idempotencia offline (Reto R1): si la operación ya se sincronizó, devolver 409 con el asiento original
        if uuid_operacion:
            previo = AsientoRepository.get_by_uuid(uuid_operacion)
            if previo:
                return False, "La operación ya fue registrada anteriormente (uuid_operacion duplicado)", 409, previo.to_dict()

        try:
            # 2. Bloqueo de la fila de la obra para correlativo seguro
            siguiente, obra = AsientoRepository.get_siguiente_correlativo_con_bloqueo(id_obra)
            if not obra or siguiente is None:
                db.session.rollback()
                return False, "Obra no encontrada", 404, None

            # 3. Validación de asignación por rol
            if not tiene_acceso_a_obra(usuario, obra):
                db.session.rollback()
                return False, "No estás asignado a esta obra", 403, None

            # 4. Punto de referencia geográfica para proximidad (frente u obra)
            ref_lat, ref_lon, ref_nombre = obra.ubicacion_lat, obra.ubicacion_lon, 'la obra'
            if id_frente:
                frente = FrenteObra.query.get(id_frente)
                if not frente or frente.id_obra != obra.id:
                    db.session.rollback()
                    return False, "El frente indicado no pertenece a esta obra", 400, None
                ref_lat, ref_lon, ref_nombre = frente.latitud, frente.longitud, 'el frente'

            # 5. Validación de proximidad (Reto R2): solo dentro del radio de obra (50m)
            if usuario.rol == 'Residente':
                radio = obra.radio_metros or 50.0
                dist = distancia_metros(lat_registro, lon_registro, ref_lat, ref_lon)
                if dist > radio:
                    db.session.rollback()
                    return False, f"Estás a {dist:.0f} m de {ref_nombre}; el radio permitido es {radio:.0f} m", 400, None

            # 6. Generación de QR inalterable
            codigo_qr = f"SITELOG-OBRA{obra.id}-AS{siguiente}-{uuid.uuid4().hex[:12].upper()}"

            nuevo = AsientoCuaderno(
                id_obra=obra.id,
                id_frente=id_frente or None,
                numero_correlativo=siguiente,
                tipo=tipo,
                titulo=titulo,
                descripcion=descripcion,
                lat_registro=lat_registro,
                lon_registro=lon_registro,
                fecha_registro=datetime.utcnow(),
                estado='Pendiente de Absolución' if tipo == 'Consulta' else 'Emitido',
                codigo_qr_verificacion=codigo_qr,
                uuid_operacion=uuid_operacion,
                id_usuario=usuario.id
            )

            asiento_creado = AsientoRepository.create_asiento(nuevo)
            return True, "Asiento registrado exitosamente", 201, asiento_creado.to_dict(include_details=True)

        except IntegrityError:
            db.session.rollback()
            return False, "Conflicto al registrar el asiento (duplicado). Intente nuevamente.", 409, None
        except Exception as e:
            db.session.rollback()
            return False, f"Error al registrar asiento: {str(e)}", 500, None

    @staticmethod
    def obtener_detalle(asiento_id: int, usuario):
        asiento = AsientoRepository.get_by_id(asiento_id)
        if not asiento:
            return False, "Asiento no encontrado", 404, None

        if not usuario or not tiene_acceso_a_obra(usuario, asiento.obra):
            return False, "No tienes autorización para ver este asiento", 403, None

        return True, None, 200, asiento.to_dict(include_details=True)

    @staticmethod
    def responder_asiento(asiento_id: int, usuario, descripcion: str, nuevo_estado: str = 'Absuelto'):
        asiento = AsientoRepository.get_by_id_with_lock(asiento_id)
        if not asiento:
            db.session.rollback()
            return False, "Asiento no encontrado", 404, None

        if not tiene_acceso_a_obra(usuario, asiento.obra):
            db.session.rollback()
            return False, "No estás asignado como supervisor de esta obra", 403, None

        desc_limpia = str(descripcion or '').strip()
        if not desc_limpia:
            db.session.rollback()
            return False, "La descripción de la absolución es obligatoria", 400, None

        estado_dest = str(nuevo_estado or 'Absuelto').strip()
        if estado_dest not in ESTADOS_RESPUESTA:
            db.session.rollback()
            return False, f"Estado inválido. Valores permitidos: {', '.join(ESTADOS_RESPUESTA)}", 400, None

        estado_previo = asiento.estado
        if estado_previo == 'Concluido' or estado_previo == estado_dest:
            db.session.rollback()
            return False, f"El asiento ya se encuentra en estado '{estado_previo}'", 409, None

        try:
            respuesta = RespuestaAsiento(
                id_asiento=asiento.id,
                id_supervisor=usuario.id,
                descripcion=desc_limpia,
                fecha_respuesta=datetime.utcnow()
            )
            AsientoRepository.add_respuesta(asiento, respuesta, estado_dest)
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
    def obtener_historial(asiento_id: int, usuario):
        asiento = AsientoRepository.get_by_id(asiento_id)
        if not asiento:
            return False, "Asiento no encontrado", 404, None

        if not usuario or not tiene_acceso_a_obra(usuario, asiento.obra):
            return False, "No tienes autorización para ver este asiento", 403, None

        historial = AsientoRepository.get_historial(asiento_id)
        return True, None, 200, [h.to_dict() for h in historial]
