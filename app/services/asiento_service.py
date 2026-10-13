import math
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.asiento import AsientoCuaderno, ESTADOS_OFICIALES
from app.models.frente import FrenteObra
from app.models.respuesta import RespuestaAsiento
from app.repositories.asiento_repository import AsientoRepository

TIPOS_VALIDOS = ['Consulta', 'Notificación', 'Instrucción', 'Modificación']

# Máquina de estados oficial (Sección 4.1 de la Versión 2)
TRANSICIONES_PERMITIDAS = {
    'PENDIENTE_SINCRONIZACION': ['EMITIDO'],
    'EMITIDO': ['OBSERVADO', 'ABSUELTO', 'CONCLUIDO'],
    'OBSERVADO': ['ABSUELTO'],
    'ABSUELTO': ['CONCLUIDO'],
    'CONCLUIDO': []  # Estado final e inmutable
}


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
    """Capa de lógica de negocio para ciclo de vida oficial, hash SHA-256, geocerca y QR."""

    @staticmethod
    def registrar_asiento(usuario, data: dict):
        id_obra = data.get('id_obra')
        tipo = str(data.get('tipo') or '').strip()
        titulo = str(data.get('titulo') or '').strip()
        descripcion = str(data.get('descripcion') or '').strip()
        lat_registro = data.get('lat_registro')
        lon_registro = data.get('lon_registro')
        accuracy_registro = data.get('accuracy_registro') if 'accuracy_registro' in data else data.get('accuracy')
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

        # 1. Idempotencia offline (Reto R1): si la operación ya se sincronizó, responder 409 con el asiento original
        if uuid_operacion:
            previo = AsientoRepository.get_by_uuid(uuid_operacion)
            if previo:
                return False, "La operación ya fue registrada anteriormente (uuid_operacion duplicado)", 409, previo.to_dict()

        try:
            # 2. Bloqueo pesimista de la fila de la obra para correlativo seguro
            siguiente, obra = AsientoRepository.get_siguiente_correlativo_con_bloqueo(id_obra)
            if not obra or siguiente is None:
                db.session.rollback()
                return False, "Obra no encontrada", 404, None

            # 3. Validación de asignación por rol
            if not tiene_acceso_a_obra(usuario, obra):
                db.session.rollback()
                return False, "No estás asignado a esta obra", 403, None

            # 4. Punto y radio de geocerca circular (frente u obra)
            ref_lat = obra.ubicacion_lat
            ref_lon = obra.ubicacion_lon
            ref_radio = obra.radio_metros or 50.0
            ref_nombre = 'la obra'

            if id_frente:
                frente = FrenteObra.query.get(id_frente)
                if not frente or frente.id_obra != obra.id:
                    db.session.rollback()
                    return False, "El frente indicado no pertenece a esta obra", 400, None
                ref_lat = frente.latitud
                ref_lon = frente.longitud
                ref_radio = frente.radio_metros or ref_radio
                ref_nombre = f"el frente '{frente.nombre_sector}'"

            # 5. Validación de Geocerca y Accuracy del GPS (Sección 6 / Reto R2)
            if usuario.rol == 'Residente':
                # Validar precisión del GPS reportada
                if accuracy_registro is not None:
                    try:
                        acc_num = float(accuracy_registro)
                        if acc_num > ref_radio:
                            db.session.rollback()
                            return False, (
                                f"La precisión del GPS ({acc_num:.1f} m) excede el radio permitido ({ref_radio:.1f} m). "
                                "Ubicación no confiable; obtenga mejor cobertura antes de asentar."
                            ), 400, None
                    except (TypeError, ValueError):
                        return False, "accuracy_registro debe ser un valor numérico", 400, None

                # Validar distancia geodésica contra el centro de la geocerca
                dist = distancia_metros(lat_registro, lon_registro, ref_lat, ref_lon)
                if dist > ref_radio:
                    db.session.rollback()
                    return False, f"Estás a {dist:.0f} m de {ref_nombre}; el radio permitido es {ref_radio:.0f} m", 400, None

            # 6. Generación del QR y cálculo del hash SHA-256 definitivo (Sección 4.2)
            ahora = datetime.utcnow().replace(microsecond=0)
            codigo_qr = f"SITELOG-OBRA{obra.id}-AS{siguiente}-{uuid.uuid4().hex[:12].upper()}"

            hash_sha256 = AsientoCuaderno.calcular_hash(
                id_obra=obra.id,
                numero_correlativo=siguiente,
                tipo=tipo,
                titulo=titulo,
                descripcion=descripcion,
                lat=lat_registro,
                lon=lon_registro,
                fecha=ahora,
                id_usuario=usuario.id
            )

            # Al persistir con éxito en el servidor pasa de inmediato a estado EMITIDO
            nuevo = AsientoCuaderno(
                id_obra=obra.id,
                id_frente=id_frente or None,
                numero_correlativo=siguiente,
                tipo=tipo,
                titulo=titulo,
                descripcion=descripcion,
                lat_registro=lat_registro,
                lon_registro=lon_registro,
                accuracy_registro=float(accuracy_registro) if accuracy_registro is not None else None,
                fecha_registro=ahora,
                estado='EMITIDO',
                hash_contenido=hash_sha256,
                codigo_qr_verificacion=codigo_qr,
                uuid_operacion=uuid_operacion,
                id_usuario=usuario.id
            )

            asiento_creado = AsientoRepository.create_asiento(nuevo)
            return True, "Asiento registrado exitosamente en estado EMITIDO con hash y QR certificados", 201, asiento_creado.to_dict(include_details=True)

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
    def responder_asiento(asiento_id: int, usuario, descripcion: str, nuevo_estado: str = 'ABSUELTO'):
        """
        POST /asientos/<id>/responder
        Absolución formal de consulta técnica por el Supervisor; transiciona el asiento a ABSUELTO.
        """
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

        estado_destino = str(nuevo_estado or 'ABSUELTO').strip().upper()
        if estado_destino not in ['ABSUELTO', 'CONCLUIDO']:
            db.session.rollback()
            return False, "La respuesta formal debe transicionar el asiento a ABSUELTO o CONCLUIDO", 400, None

        # Validación de máquina de estados: solo aplica sobre EMITIDO u OBSERVADO
        if asiento.estado not in ['EMITIDO', 'OBSERVADO']:
            db.session.rollback()
            return False, f"No se puede absolver un asiento en estado '{asiento.estado}' (debe estar en EMITIDO u OBSERVADO)", 409, None

        try:
            respuesta = RespuestaAsiento(
                id_asiento=asiento.id,
                id_supervisor=usuario.id,
                descripcion=desc_limpia,
                fecha_respuesta=datetime.utcnow()
            )
            AsientoRepository.add_respuesta(asiento, respuesta, estado_destino)
            return True, f"Absolución registrada exitosamente. Asiento transicionado a {estado_destino}", 200, asiento.to_dict(include_details=True)

        except Exception as e:
            db.session.rollback()
            return False, f"Error al procesar respuesta: {str(e)}", 500, None

    @staticmethod
    def cambiar_estado(asiento_id: int, usuario, nuevo_estado: str, comentario: str = None):
        """
        PUT /asientos/<id>/estado
        Aplica una transición válida según la máquina de estados oficial de 4.1.
        Valida permisos de rol según la transición.
        """
        asiento = AsientoRepository.get_by_id_with_lock(asiento_id)
        if not asiento:
            db.session.rollback()
            return False, "Asiento no encontrado", 404, None

        if not tiene_acceso_a_obra(usuario, asiento.obra):
            db.session.rollback()
            return False, "No tienes autorización sobre esta obra", 403, None

        estado_dest = str(nuevo_estado or '').strip().upper()
        if estado_dest not in ESTADOS_OFICIALES:
            db.session.rollback()
            return False, f"Estado inválido. Estados oficiales: {', '.join(ESTADOS_OFICIALES)}", 400, None

        estado_actual = asiento.estado

        # 1. Regla de inmutabilidad de CONCLUIDO
        if estado_actual == 'CONCLUIDO':
            db.session.rollback()
            return False, "El asiento ya se encuentra en estado final e inmutable CONCLUIDO; no admite más transiciones", 409, None

        if estado_actual == estado_dest:
            db.session.rollback()
            return False, f"El asiento ya se encuentra en estado '{estado_actual}'", 409, None

        # 2. Validación contra la máquina de estados oficial
        permitidas = TRANSICIONES_PERMITIDAS.get(estado_actual, [])
        if estado_dest not in permitidas:
            db.session.rollback()
            return False, f"Transición no permitida: no se puede cambiar de {estado_actual} a {estado_dest}", 400, None

        # 3. Reglas de control por rol sobre la transición (Sección 4.1)
        if estado_dest == 'OBSERVADO' and usuario.rol not in ['Supervisor', 'Administrador']:
            db.session.rollback()
            return False, "Solo el Supervisor o Administrador pueden marcar un asiento como OBSERVADO", 403, None

        if estado_dest == 'CONCLUIDO' and estado_actual == 'EMITIDO':
            # Solo Administrador para tipos que no requieren absolución (Notificación/Instrucción)
            if usuario.rol != 'Administrador':
                db.session.rollback()
                return False, "Solo el Administrador Contractual puede concluir directamente asientos tipo Notificación/Instrucción", 403, None

        try:
            asiento_actualizado = AsientoRepository.cambiar_estado(
                asiento=asiento,
                nuevo_estado=estado_dest,
                usuario_id=usuario.id,
                comentario=comentario
            )
            return True, f"Asiento transicionado exitosamente a {estado_dest}", 200, asiento_actualizado.to_dict(include_details=True)

        except Exception as e:
            db.session.rollback()
            return False, f"Error al cambiar estado del asiento: {str(e)}", 500, None

    @staticmethod
    def verificar_qr(codigo_qr: str):
        """
        GET /asientos/verificar/<codigo_qr>
        Contrasta el hash SHA-256 del contenido actual contra hash_contenido (Sección 4.2).
        Detecta adulteraciones directas en la base de datos.
        """
        asiento = AsientoRepository.get_by_qr(codigo_qr)
        if not asiento:
            return False, "Código QR no reconocido o no registrado en el Cuaderno de Obra oficial", 404, None

        es_autentico = asiento.verificar_integridad()

        data = {
            'valido': es_autentico,
            'integro': es_autentico,
            'mensaje': "Documento digital oficial certificado e inalterable" if es_autentico else "Alerta de seguridad: el contenido del asiento ha sido adulterado o modificado en base de datos",
            'hash_contenido': asiento.hash_contenido,
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
