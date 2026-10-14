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
    Registra un asiento a partir de uuid_operacion (idempotente).
    Valida geocerca y accuracy del GPS, calcula hash SHA-256 inmutable y genera código QR al pasar a EMITIDO.
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
    Detalle completo del asiento incluyendo respuestas, incidencias y evidencias.
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
    Absolución formal de consulta técnica por el Supervisor; transiciona el asiento a ABSUELTO.
    """
    usuario = get_current_user()
    data = request.get_json(silent=True) or {}
    descripcion = data.get('descripcion', '')
    nuevo_estado = data.get('estado', 'ABSUELTO')

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
# 4. PUT /asientos/<id>/estado (NUEVO endpoint Sección 9 - Versión 2)
# ---------------------------------------------------------------------------
@asientos_bp.route('/<int:id>/estado', methods=['PUT'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def cambiar_estado_asiento(id):
    """
    PUT /asientos/<id>/estado
    Aplica una transición válida según la máquina de estados de la sección 4.1.
    (Ej: EMITIDO -> OBSERVADO, ABSUELTO -> CONCLUIDO).
    Valida en servidor que la transición esté permitida para el rol solicitante.
    """
    usuario = get_current_user()
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get('nuevo_estado') or data.get('estado', '')
    comentario = data.get('comentario', '')

    success, message, status_code, asiento_data = AsientoService.cambiar_estado(
        asiento_id=id,
        usuario=usuario,
        nuevo_estado=nuevo_estado,
        comentario=comentario
    )

    if not success:
        return jsonify({'success': False, 'error': message}), status_code

    return jsonify({
        'success': True,
        'message': message,
        'asiento': asiento_data
    }), status_code


# ---------------------------------------------------------------------------
# 5. POST /asientos/<id>/incidencias
# ---------------------------------------------------------------------------
@asientos_bp.route('/<int:id>/incidencias', methods=['POST'])
@jwt_required()
@role_required(['Residente', 'Supervisor', 'Administrador'])
def registrar_incidencia(id):
    """
    POST /asientos/<id>/incidencias
    Registro de incidencia técnica con foto opcional (multipart/form-data o JSON).
    """
    user_id = int(get_jwt_identity())

    if request.is_json:
        data = request.get_json() or {}
        tipo_incidencia = data.get('tipo') or data.get('tipo_incidencia', '')
        descripcion = data.get('descripcion', '')
        impacto_contractual = data.get('impacto_contractual')
        foto_file = None
    else:
        tipo_incidencia = request.form.get('tipo') or request.form.get('tipo_incidencia', '')
        descripcion = request.form.get('descripcion', '')
        impacto_contractual = request.form.get('impacto_contractual')
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
        'asiento': inc_data.get('asiento', id),
        'tipo': inc_data.get('tipo'),
        'estado': inc_data.get('estado', 'ABIERTA'),
        'incidencia': inc_data
    }), status_code


# ---------------------------------------------------------------------------
# 6. GET /asientos/<id>/historial
# ---------------------------------------------------------------------------
@asientos_bp.route('/<int:id>/historial', methods=['GET'])
@jwt_required()
def historial_asiento(id):
    """
    GET /asientos/<id>/historial
    Trazabilidad cronológica de cambios y auditoría contractual del asiento.
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
# 7. GET /asientos/verificar/<codigo_qr> (Público)
# ---------------------------------------------------------------------------
@asientos_bp.route('/verificar/<string:codigo_qr>', methods=['GET'])
def verificar_codigo_qr(codigo_qr):
    """
    GET /asientos/verificar/<codigo_qr>
    Endpoint público de verificación: recalcula el hash SHA-256 del contenido actual
    y lo contrasta contra hash_contenido para certificar autenticidad e inalterabilidad (Sección 4.2).
    """
    success, error_msg, status_code, data = AsientoService.verificar_qr(codigo_qr)

    if not success:
        return jsonify({
            'success': False,
            'valido': False,
            'integro': False,
            'error': error_msg
        }), status_code

    response = {'success': True}
    response.update(data)
    return jsonify(response), 200
