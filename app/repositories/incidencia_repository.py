from app.extensions import db
from app.models.incidencia import IncidenciaObra
from app.models.evidencia import Evidencia

class IncidenciaRepository:
    """Capa de acceso a datos para la entidad IncidenciaObra y Evidencias."""

    @staticmethod
    def get_by_id(incidencia_id: int):
        return IncidenciaObra.query.get(incidencia_id)

    @staticmethod
    def get_all(id_asiento: int = None):
        query = IncidenciaObra.query
        if id_asiento is not None:
            query = query.filter_by(id_asiento=id_asiento)
        return query.order_by(IncidenciaObra.fecha_registro.desc()).all()

    @staticmethod
    def create(incidencia: IncidenciaObra, evidencia: Evidencia = None):
        db.session.add(incidencia)
        db.session.flush()

        if evidencia:
            evidencia.id_incidencia = incidencia.id
            db.session.add(evidencia)

        db.session.commit()
        return incidencia

    @staticmethod
    def update(incidencia: IncidenciaObra, observacion: str = None, impacto: str = None, tipo: str = None):
        if impacto:
            incidencia.impacto_contractual = impacto.strip()
        if tipo:
            incidencia.tipo_incidencia = tipo.strip()
        if observacion:
            incidencia.descripcion = f"{incidencia.descripcion} [Obs. Supervisor: {observacion.strip()}]"

        db.session.commit()
        return incidencia

    @staticmethod
    def delete(incidencia: IncidenciaObra):
        db.session.delete(incidencia)
        db.session.commit()
        return True
