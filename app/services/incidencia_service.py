import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.incidencia import IncidenciaObra
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
    def registrar_en_asiento(asiento_id: int, user_id: int, tipo_incidencia: str, descripcion: str, impacto_contractual: str, foto_file = None, upload_folder: str = 'uploads'):
        asiento = AsientoRepository.get_by_id(asiento_id)
        if not asiento:
            return False, "Asiento no encontrado", 404, None

        if not all([tipo_incidencia, descripcion, impacto_contractual]):
            return False, "tipo_incidencia, descripcion e impacto_contractual son obligatorios", 400, None

        try:
            incidencia = IncidenciaObra(
                id_asiento=asiento.id,
                tipo_incidencia=tipo_incidencia.strip(),
                descripcion=descripcion.strip(),
                impacto_contractual=impacto_contractual.strip(),
                fecha_registro=datetime.utcnow()
            )

            evidencia = None
            if foto_file and foto_file.filename != '':
                filename = secure_filename(f"inc_{uuid.uuid4().hex[:8]}_{foto_file.filename}")
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                foto_file.save(file_path)

                evidencia = Evidencia(
                    id_asiento=asiento.id,
                    ruta_archivo=filename,
                    tipo='IMAGEN',
                    fecha=datetime.utcnow()
                )

            incidencia_creada = IncidenciaRepository.create(incidencia, evidencia=evidencia)
            return True, "Incidencia registrada exitosamente", 201, incidencia_creada.to_dict(include_evidencias=True)

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
