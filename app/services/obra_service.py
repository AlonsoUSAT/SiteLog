from datetime import datetime
from app.repositories.obra_repository import ObraRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.asiento_repository import AsientoRepository

class ObraService:
    """Capa de lógica de negocio para obras, frentes y consultas de asientos."""

    @staticmethod
    def listar_obras(user_id: int, estado: str = None, id_residente: int = None):
        usuario = UsuarioRepository.get_by_id(user_id)
        if not usuario:
            return False, "Usuario no válido o sesión expirada", 401, None

        obras = ObraRepository.get_all(usuario, estado=estado, id_residente=id_residente)
        return True, None, 200, [obra.to_dict(include_frentes=True) for obra in obras]

    @staticmethod
    def obtener_detalle_obra(obra_id: int, user_id: int):
        usuario = UsuarioRepository.get_by_id(user_id)
        if not usuario:
            return False, "Usuario no válido", 401, None

        obra = ObraRepository.get_by_id(obra_id)
        if not obra:
            return False, f"Obra con ID {obra_id} no encontrada", 404, None

        # Regla de autorización por rol
        if usuario.rol == 'Residente' and obra.id_residente != usuario.id:
            return False, "No tienes autorización para acceder a esta obra", 403, None

        if usuario.rol == 'Supervisor' and obra.id_supervisor != usuario.id:
            return False, "No estás asignado como supervisor de esta obra", 403, None

        resumen = ObraRepository.get_metricas_resumen(obra_id)
        data = obra.to_dict(include_frentes=True)
        data['resumen'] = resumen
        return True, None, 200, data

    @staticmethod
    def listar_asientos_obra(obra_id: int, user_id: int, tipo: str = None, estado: str = None, id_frente: int = None, fecha_inicio_str: str = None, fecha_fin_str: str = None):
        usuario = UsuarioRepository.get_by_id(user_id)
        if not usuario:
            return False, "Usuario no válido", 401, None

        obra = ObraRepository.get_by_id(obra_id)
        if not obra:
            return False, f"Obra con ID {obra_id} no encontrada", 404, None

        if usuario.rol == 'Residente' and obra.id_residente != usuario.id:
            return False, "No tienes autorización para consultar asientos de esta obra", 403, None

        if usuario.rol == 'Supervisor' and obra.id_supervisor != usuario.id:
            return False, "No estás asignado a esta obra", 403, None

        fecha_inicio = None
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str.strip()[:10], '%Y-%m-%d')
            except ValueError:
                return False, "Formato de fecha_inicio inválido (use YYYY-MM-DD)", 400, None

        fecha_fin = None
        if fecha_fin_str:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str.strip()[:10] + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return False, "Formato de fecha_fin inválido (use YYYY-MM-DD)", 400, None

        asientos = AsientoRepository.get_asientos_by_obra(
            id_obra=obra_id,
            tipo=tipo,
            estado=estado,
            id_frente=id_frente,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        return True, None, 200, {
            'id_obra': obra_id,
            'obra_nombre': obra.nombre,
            'total': len(asientos),
            'asientos': [asiento.to_dict() for asiento in asientos]
        }
