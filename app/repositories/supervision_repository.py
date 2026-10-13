from app.models.obra import Obra
from app.models.asiento import AsientoCuaderno
from app.models.incidencia import IncidenciaObra

class SupervisionRepository:
    """Capa de acceso a datos para métricas consolidadas y KPIs contractuales."""

    @staticmethod
    def get_kpis_contractuales():
        total_obras = Obra.query.count()
        obras_en_ejecucion = Obra.query.filter_by(estado='En ejecución').count()
        obras_con_observaciones = Obra.query.filter_by(estado='Con observaciones').count()
        obras_paralizadas = Obra.query.filter_by(estado='Paralizada').count()
        obras_concluidas = Obra.query.filter_by(estado='Concluida').count()

        total_asientos = AsientoCuaderno.query.count()
        consultas_pendientes = AsientoCuaderno.query.filter_by(
            tipo='Consulta', estado='Pendiente de Absolución'
        ).count()

        asientos_emitidos = AsientoCuaderno.query.filter_by(estado='Emitido').count()
        asientos_absueltos = AsientoCuaderno.query.filter_by(estado='Absuelto').count()
        asientos_observados = AsientoCuaderno.query.filter_by(estado='Observado').count()

        total_incidencias = IncidenciaObra.query.count()

        return {
            'total_obras': total_obras,
            'obras_en_ejecucion': obras_en_ejecucion,
            'obras_con_observaciones': obras_con_observaciones,
            'obras_paralizadas': obras_paralizadas,
            'obras_concluidas': obras_concluidas,
            'total_asientos': total_asientos,
            'consultas_pendientes': consultas_pendientes,
            'asientos_emitidos': asientos_emitidos,
            'asientos_absueltos': asientos_absueltos,
            'asientos_observados': asientos_observados,
            'total_incidencias': total_incidencias
        }
