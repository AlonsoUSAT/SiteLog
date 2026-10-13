from app.repositories.supervision_repository import SupervisionRepository
from app.repositories.usuario_repository import UsuarioRepository

class SupervisionService:
    """Capa de lógica de negocio para monitoreo, indicadores contractuales y gestión de usuarios."""

    @staticmethod
    def obtener_kpis():
        try:
            kpis = SupervisionRepository.get_kpis_contractuales()
            return True, None, 200, kpis
        except Exception as e:
            return False, f"Error al calcular KPIs contractuales: {str(e)}", 500, None

    @staticmethod
    def listar_residentes():
        try:
            residentes = UsuarioRepository.get_residentes_activos()
            return True, None, 200, [r.to_dict() for r in residentes]
        except Exception as e:
            return False, f"Error al consultar residentes: {str(e)}", 500, None
