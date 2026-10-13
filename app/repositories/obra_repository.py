from app.extensions import db
from app.models.obra import Obra
from app.models.asiento import AsientoCuaderno
from app.models.incidencia import IncidenciaObra

class ObraRepository:
    """Capa de acceso a datos para la entidad Obra."""

    @staticmethod
    def get_by_id(obra_id: int):
        return Obra.query.get(obra_id)

    @staticmethod
    def get_all(usuario, estado: str = None, id_residente: int = None):
        query = Obra.query

        if usuario.rol == 'Residente':
            query = query.filter(Obra.id_residente == usuario.id)
        elif usuario.rol == 'Supervisor':
            query = query.filter(Obra.id_supervisor == usuario.id)

        if estado:
            query = query.filter(Obra.estado == estado.strip())

        if id_residente and usuario.rol == 'Administrador':
            query = query.filter(Obra.id_residente == id_residente)

        return query.order_by(Obra.id.desc()).all()

    @staticmethod
    def get_metricas_resumen(obra_id: int):
        total_asientos = AsientoCuaderno.query.filter_by(id_obra=obra_id).count()
        asientos_emitidos = AsientoCuaderno.query.filter_by(id_obra=obra_id, estado='Emitido').count()
        asientos_pendientes = AsientoCuaderno.query.filter_by(id_obra=obra_id, estado='Pendiente de Absolución').count()
        asientos_absueltos = AsientoCuaderno.query.filter_by(id_obra=obra_id, estado='Absuelto').count()
        asientos_observados = AsientoCuaderno.query.filter_by(id_obra=obra_id, estado='Observado').count()
        asientos_concluidos = AsientoCuaderno.query.filter_by(id_obra=obra_id, estado='Concluido').count()

        total_incidencias = (
            IncidenciaObra.query
            .join(AsientoCuaderno, IncidenciaObra.id_asiento == AsientoCuaderno.id)
            .filter(AsientoCuaderno.id_obra == obra_id)
            .count()
        )

        return {
            'total_asientos': total_asientos,
            'asientos_emitidos': asientos_emitidos,
            'asientos_pendientes': asientos_pendientes,
            'asientos_absueltos': asientos_absueltos,
            'asientos_observados': asientos_observados,
            'asientos_concluidos': asientos_concluidos,
            'total_incidencias': total_incidencias
        }
