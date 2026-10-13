from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import role_required, get_current_user
from app.services.asiento_service import AsientoService
from app.services.incidencia_service import IncidenciaService

asientos_bp = Blueprint('asientos', __name__, url_prefix='/asientos')


# ---------------------------------------------------------------------------
# 1. POST /asientos
# ---------------------------------------------------------------------------
@asientos_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['Residente', 'Administrador'])
def registrar_asiento():
    """
    POST /asientos
    Capa Route: Registra nuevo asiento con validación de proximidad y correlativo transaccional.
    Idempotencia offline: 409 con el asiento original si se repite 'uuid_operacion'.
    """
    usuario = get_current_user()
    data = request.get_json(silent=True) or {}

    success, message, status_code, result_data = AsientoService.registrar_asiento(usuario, data)

    if not success:
        resp = {'success': False, 'error': message}
        if status_code == 409 and result_data:
            resp['asiento'] = result_data
        return jsonify(resp), status_code

    return jsonify({
        'success': True,
        'message': message,
        'asiento': result_data
    }), status_code


# ---------------------------------------------------------------------------
# 2. GET /asientos/<id>
# ---------------------------------------------------------------------------
@asientos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def detalle_asiento(id):
    """
    GET /asientos/<id>
    Capa Route: Detalle completo del asiento incluyendo respuestas, incidencias y evidencias.
    """
    usuario = get_current_user()
    success, error_msg, status_code, data = AsientoService.obtener_detalle(id, usuario)

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'asiento': data
    }), 200


# ---------------------------------------------------------------------------
# 3. POST /asientos/<id>/responder
# ---------------------------------------------------------------------------
@asientos_bp.route('/<int:id>/responder', methods=['POST'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def responder_asiento(id):
    """
    POST /asientos/<id>/responder
    Capa Route: Absolución formal del supervisor delegando a AsientoService.
    """
    usuario = get_current_user()
    data = request.get_json(silent=True) or {}
    descripcion = data.get('descripcion', '')
    nuevo_estado = data.get('estado', 'Absuelto')

    success, message, status_code, asiento_data = AsientoService.responder_asiento(
        asiento_id=id,
        usuario=usuario,
        descripcion=descripcion,
        nuevo_estado=nuevo_estado
    )

    if not success:
        return jsonify({'success': False, 'error': message}), status_code

    return jsonify({
        'success': True,
        'message': message,
        'asiento': asiento_data
    }), status_code


# ---------------------------------------------------------------------------
# (Bloque de Dana) POST /asientos/<id>/incidencias
# ---------------------------------------------------------------------------
@asientos_bp.route('/<int:id>/incidencias', methods=['POST'])
@jwt_required()
@role_required(['Residente', 'Supervisor', 'Administrador'])
def registrar_incidencia(id):
    """
    POST /asientos/<id>/incidencias
    Capa Route: Registro de incidencia técnica con foto opcional delegando a IncidenciaService.
    """
    user_id = int(get_jwt_identity())

    if request.is_json:
        data = request.get_json() or {}
        tipo_incidencia = data.get('tipo_incidencia', '')
        descripcion = data.get('descripcion', '')
        impacto_contractual = data.get('impacto_contractual', '')
        foto_file = None
    else:
        tipo_incidencia = request.form.get('tipo_incidencia', '')
        descripcion = request.form.get('descripcion', '')
        impacto_contractual = request.form.get('impacto_contractual', '')
        foto_file = request.files.get('evidencia_foto')

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    success, message, status_code, inc_data = IncidenciaService.registrar_en_asiento(
        asiento_id=id,
        user_id=user_id,
        tipo_incidencia=tipo_incidencia,
        descripcion=descripcion,
        impacto_contractual=impacto_contractual,
        foto_file=foto_file,
        upload_folder=upload_folder
    )

    if not success:
        return jsonify({'success': False, 'error': message}), status_code

    return jsonify({
        'success': True,
        'message': message,
        'incidencia': inc_data
    }), status_code


# ---------------------------------------------------------------------------
# 5. GET /asientos/<id>/historial
# ---------------------------------------------------------------------------
@asientos_bp.route('/<int:id>/historial', methods=['GET'])
@jwt_required()
def historial_asiento(id):
    """
    GET /asientos/<id>/historial
    Capa Route: Trazabilidad cronológica de cambios y auditoría contractual del asiento.
    """
    usuario = get_current_user()
    success, error_msg, status_code, historial = AsientoService.obtener_historial(id, usuario)

    if not success:
        return jsonify({'success': False, 'error': error_msg}), status_code

    return jsonify({
        'success': True,
        'id_asiento': id,
        'historial': historial
    }), 200


# ---------------------------------------------------------------------------
# 4. GET /asientos/verificar/<codigo_qr> (Público)
# ---------------------------------------------------------------------------
@asientos_bp.route('/verificar/<string:codigo_qr>', methods=['GET'])
def verificar_codigo_qr(codigo_qr):
    """
    GET /asientos/verificar/<codigo_qr>
    Capa Route: Verificación pública de autenticidad inalterable por QR delegando a AsientoService.
    """
    success, error_msg, status_code, data = AsientoService.verificar_qr(codigo_qr)

    if not success:
        return jsonify({
            'success': False,
            'valido': False,
            'error': error_msg
        }), status_code

    response = {'success': True}
    response.update(data)
    return jsonify(response), 200
