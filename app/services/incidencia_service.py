import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.incidencia import IncidenciaObra, CATALOGO_TIPOS_INCIDENCIA
from app.models.evidencia import Evidencia
from app.repositories.incidencia_repository import IncidenciaRepository
from app.repositories.asiento_repository import AsientoRepository

class IncidenciaService:
    """Capa de lógica de negocio para contingencias técnicas, evidencias fotográficas y observaciones."""

    @staticmethod
    def listar(id_asiento: int = None):
        incidencias = IncidenciaRepository.get_all(id_asiento=id_asiento)
        return True, None, 200, [inc.to_dict(include_evidencias=True) for inc in incidencias]

    @staticmethod
    def obtener_detalle(incidencia_id: int):
        incidencia = IncidenciaRepository.get_by_id(incidencia_id)
        if not incidencia:
            return False, "Incidencia no encontrada", 404, None
        return True, None, 200, incidencia.to_dict(include_evidencias=True)

    @staticmethod
    def registrar_en_asiento(asiento_id: int, user_id: int, tipo_incidencia: str, descripcion: str, impacto_contractual: str = None, foto_file = None, upload_folder: str = 'uploads'):
        # 1. Verificar que el asiento exista (si no, 404)
        try:
            asiento_id_int = int(asiento_id)
            if asiento_id_int <= 0:
                return False, "ID de asiento inválido", 400, None
        except (ValueError, TypeError):
            return False, "ID de asiento debe ser numérico", 400, None

        asiento = AsientoRepository.get_by_id(asiento_id_int)
        if not asiento:
            return False, f"Asiento con ID {asiento_id} no encontrado", 404, None

        # 2. Validar que tipo y descripción sean obligatorios y no vacíos
        tipo_str = str(tipo_incidencia or '').strip()
        desc_str = str(descripcion or '').strip()

        if not desc_str:
            return False, "La descripción de la incidencia es obligatoria y no puede estar vacía", 400, None

        if not tipo_str:
            return False, "El tipo de incidencia es obligatorio y no puede estar vacío", 400, None

        # 3. Validar que el tipo pertenezca al catálogo del proyecto
        tipo_normalizado = None
        for cat in CATALOGO_TIPOS_INCIDENCIA:
            if cat.lower() == tipo_str.lower():
                tipo_normalizado = cat
                break

        if not tipo_normalizado:
            return False, f"El tipo '{tipo_str}' no pertenece al catálogo válido del proyecto. Valores permitidos: {', '.join(CATALOGO_TIPOS_INCIDENCIA)}", 400, None

        # 4. Registrar la incidencia con estado inicial ABIERTA y fecha/hora (sin modificar otros estados)
        try:
            ahora = datetime.utcnow().replace(microsecond=0)
            impacto_final = str(impacto_contractual or '').strip() or 'Por evaluar'

            incidencia = IncidenciaObra(
                id_asiento=asiento.id,
                tipo_incidencia=tipo_normalizado,
                descripcion=desc_str,
                impacto_contractual=impacto_final,
                fecha_registro=ahora,
                estado='ABIERTA'
            )

            evidencia = None
            if foto_file and hasattr(foto_file, 'filename') and foto_file.filename != '':
                filename = secure_filename(f"inc_{uuid.uuid4().hex[:8]}_{foto_file.filename}")
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                foto_file.save(file_path)

                evidencia = Evidencia(
                    id_asiento=asiento.id,
                    ruta_archivo=filename,
                    tipo='IMAGEN',
                    fecha=ahora
                )

            incidencia_creada = IncidenciaRepository.create(incidencia, evidencia=evidencia)

            data_resp = {
                'id': incidencia_creada.id,
                'asiento': asiento.id,
                'id_asiento': asiento.id,
                'tipo': incidencia_creada.tipo_incidencia,
                'tipo_incidencia': incidencia_creada.tipo_incidencia,
                'descripcion': incidencia_creada.descripcion,
                'impacto_contractual': incidencia_creada.impacto_contractual,
                'estado': incidencia_creada.estado,
                'fecha_registro': incidencia_creada.fecha_registro.isoformat() if incidencia_creada.fecha_registro else None
            }
            if evidencia:
                data_resp['evidencias'] = [evidencia.to_dict()]

            return True, "Incidencia registrada exitosamente con estado ABIERTA", 201, data_resp

        except Exception as e:
            db.session.rollback()
            return False, f"Error al registrar incidencia: {str(e)}", 500, None

    @staticmethod
    def actualizar_estado(incidencia_id: int, observacion: str = None, impacto: str = None, tipo: str = None):
        incidencia = IncidenciaRepository.get_by_id(incidencia_id)
        if not incidencia:
            return False, "Incidencia no encontrada", 404, None

        if not any([observacion, impacto, tipo]):
            return False, "Debe proporcionar al menos un campo para actualizar: observacion, impacto_contractual o tipo_incidencia", 400, None

        try:
            incidencia_actualizada = IncidenciaRepository.update(
                incidencia,
                observacion=observacion,
                impacto=impacto,
                tipo=tipo
            )
            return True, "Incidencia actualizada correctamente", 200, incidencia_actualizada.to_dict(include_evidencias=True)

        except Exception as e:
            db.session.rollback()
            return False, f"Error al actualizar incidencia: {str(e)}", 500, None

    @staticmethod
    def eliminar(incidencia_id: int, usuario):
        """
        DELETE /incidencias/<id>
        Eliminación controlada de incidencia preliminar con validación contractual.
        Bloquea eliminación si el asiento ya se encuentra CONCLUIDO o ABSUELTO (409 Conflict).
        """
        incidencia = IncidenciaRepository.get_by_id(incidencia_id)
        if not incidencia:
            return False, "Incidencia no encontrada", 404, None

        asiento = incidencia.asiento
        # 1. Validación de autorización por rol
        if usuario.rol == 'Residente' and asiento.id_usuario != usuario.id:
            return False, "No estás autorizado para eliminar incidencias registradas por otro usuario", 403, None

        # 2. Validación de regla de negocio: inalterabilidad en estados avanzados
        if asiento.estado == 'CONCLUIDO':
            return False, "No se puede eliminar una incidencia de un asiento en estado CONCLUIDO (expediente formal inalterable)", 409, None

        if asiento.estado == 'ABSUELTO' and usuario.rol == 'Residente':
            return False, "No se puede eliminar una incidencia asociada a un asiento que ya ha sido absuelto", 409, None

        try:
            IncidenciaRepository.delete(incidencia)
            return True, f"Incidencia #{incidencia_id} eliminada exitosamente", 200, {'id_eliminado': incidencia_id}

        except Exception as e:
            db.session.rollback()
            return False, f"Error al eliminar incidencia: {str(e)}", 500, None
