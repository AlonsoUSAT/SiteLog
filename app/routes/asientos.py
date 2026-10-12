import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.asiento import AsientoCuaderno
from app.models.obra import Obra
from app.models.respuesta import RespuestaAsiento
from app.models.incidencia import IncidenciaObra
from app.models.evidencia import Evidencia
from app.models.historial import HistorialCambio
from app.utils.decorators import role_required

asientos_bp = Blueprint('asientos', __name__, url_prefix='/asientos')

@asientos_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['Residente', 'Administrador'])
def registrar_asiento():
    """
    POST /asientos
    Registra un nuevo asiento con correlativo transaccional automático por obra.
    Genera un token/código QR único de verificación inalterable.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    id_obra = data.get('id_obra')
    tipo = data.get('tipo', '').strip()  # 'Consulta', 'Notificación', 'Instrucción', 'Modificación'
    titulo = data.get('titulo', '').strip()
    descripcion = data.get('descripcion', '').strip()
    lat_registro = data.get('lat_registro')
    lon_registro = data.get('lon_registro')
    id_frente = data.get('id_frente')

    if not all([id_obra, tipo, titulo, descripcion, lat_registro is not None, lon_registro is not None]):
        return jsonify({
            'success': False,
            'error': 'Faltan campos obligatorios: id_obra, tipo, titulo, descripcion, lat_registro, lon_registro'
        }), 400

    obra = Obra.query.get(id_obra)
    if not obra:
        return jsonify({'success': False, 'error': 'Obra no encontrada'}), 404

    # Transacción para calcular correlativo consecutivo seguro evitando colisiones
    try:
        ultimo_asiento = (
            AsientoCuaderno.query
            .filter_by(id_obra=id_obra)
            .order_by(AsientoCuaderno.numero_correlativo.desc())
            .with_for_update()
            .first()
        )
        siguiente_correlativo = (ultimo_asiento.numero_correlativo + 1) if ultimo_asiento else 1

        # Generar identificador único de verificación documental para QR
        codigo_qr = f"SITELOG-OBRA{id_obra}-AS{siguiente_correlativo}-{uuid.uuid4().hex[:12].upper()}"

        nuevo_asiento = AsientoCuaderno(
            id_obra=id_obra,
            id_frente=id_frente,
            numero_correlativo=siguiente_correlativo,
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            lat_registro=float(lat_registro),
            lon_registro=float(lon_registro),
            fecha_registro=datetime.utcnow(),
            estado='Pendiente de Absolución' if tipo == 'Consulta' else 'Emitido',
            codigo_qr_verificacion=codigo_qr,
            id_usuario=user_id
        )

        db.session.add(nuevo_asiento)
        db.session.flush()

        # Registrar historial inicial
        historial = HistorialCambio(
            id_asiento=nuevo_asiento.id,
            estado_anterior=None,
            estado_nuevo=nuevo_asiento.estado,
            comentario='Registro inicial de asiento en cuaderno de obra digital',
            id_usuario=user_id,
            fecha=datetime.utcnow()
        )
        db.session.add(historial)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Asiento registrado exitosamente',
            'asiento': nuevo_asiento.to_dict(include_details=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al registrar asiento: {str(e)}'}), 500


@asientos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def detalle_asiento(id):
    """
    GET /asientos/<id>
    Detalle completo del asiento incluyendo respuestas, incidencias y evidencias.
    """
    asiento = AsientoCuaderno.query.get(id)
    if not asiento:
        return jsonify({'success': False, 'error': 'Asiento no encontrado'}), 404

    return jsonify({
        'success': True,
        'asiento': asiento.to_dict(include_details=True)
    }), 200


@asientos_bp.route('/<int:id>/responder', methods=['POST'])
@jwt_required()
@role_required(['Supervisor', 'Administrador'])
def responder_asiento(id):
    """
    POST /asientos/<id>/responder
    Absolución formal de consulta técnica por parte del supervisor.
    Actualiza el estado del asiento a 'Absuelto' o 'Concluido'.
    """
    user_id = int(get_jwt_identity())
    asiento = AsientoCuaderno.query.get(id)
    if not asiento:
        return jsonify({'success': False, 'error': 'Asiento no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    descripcion = data.get('descripcion', '').strip()
    nuevo_estado = data.get('estado', 'Absuelto').strip()

    if not descripcion:
        return jsonify({'success': False, 'error': 'La descripción de la absolución es obligatoria'}), 400

    try:
        estado_previo = asiento.estado

        # Registrar respuesta formal
        respuesta = RespuestaAsiento(
            id_asiento=asiento.id,
            id_supervisor=user_id,
            descripcion=descripcion,
            fecha_respuesta=datetime.utcnow()
        )
        db.session.add(respuesta)

        # Actualizar estado de asiento
        asiento.estado = nuevo_estado

        # Registrar trazabilidad en historial
        historial = HistorialCambio(
            id_asiento=asiento.id,
            estado_anterior=estado_previo,
            estado_nuevo=asiento.estado,
            comentario=f'Absolución formal registrada por supervisor: {descripcion[:100]}...',
            id_usuario=user_id,
            fecha=datetime.utcnow()
        )
        db.session.add(historial)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Absolución registrada exitosamente',
            'asiento': asiento.to_dict(include_details=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al procesar respuesta: {str(e)}'}), 500


@asientos_bp.route('/<int:id>/incidencias', methods=['POST'])
@jwt_required()
@role_required(['Residente', 'Supervisor', 'Administrador'])
def registrar_incidencia(id):
    """
    POST /asientos/<id>/incidencias
    Registra una incidencia técnica vinculada a un asiento.
    Admite multipart/form-data con archivo fotográfico opcional.
    """
    user_id = int(get_jwt_identity())
    asiento = AsientoCuaderno.query.get(id)
    if not asiento:
        return jsonify({'success': False, 'error': 'Asiento no encontrado'}), 404

    # Admite JSON o Multipart Form
    if request.is_json:
        data = request.get_json() or {}
        tipo_incidencia = data.get('tipo_incidencia', '').strip()
        descripcion = data.get('descripcion', '').strip()
        impacto_contractual = data.get('impacto_contractual', '').strip()
        foto_file = None
    else:
        tipo_incidencia = request.form.get('tipo_incidencia', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        impacto_contractual = request.form.get('impacto_contractual', '').strip()
        foto_file = request.files.get('evidencia_foto')

    if not all([tipo_incidencia, descripcion, impacto_contractual]):
        return jsonify({
            'success': False,
            'error': 'tipo_incidencia, descripcion e impacto_contractual son obligatorios'
        }), 400

    try:
        incidencia = IncidenciaObra(
            id_asiento=asiento.id,
            tipo_incidencia=tipo_incidencia,
            descripcion=descripcion,
            impacto_contractual=impacto_contractual,
            fecha_registro=datetime.utcnow()
        )
        db.session.add(incidencia)
        db.session.flush()

        # Si se adjuntó archivo de evidencia fotográfica
        if foto_file and foto_file.filename != '':
            filename = secure_filename(f"inc_{incidencia.id}_{uuid.uuid4().hex[:8]}_{foto_file.filename}")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            foto_file.save(file_path)

            evidencia = Evidencia(
                id_asiento=asiento.id,
                id_incidencia=incidencia.id,
                ruta_archivo=filename,
                tipo='IMAGEN',
                fecha=datetime.utcnow()
            )
            db.session.add(evidencia)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Incidencia registrada exitosamente',
            'incidencia': incidencia.to_dict(include_evidencias=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al registrar incidencia: {str(e)}'}), 500


@asientos_bp.route('/<int:id>/historial', methods=['GET'])
@jwt_required()
def historial_asiento(id):
    """
    GET /asientos/<id>/historial
    Trazabilidad de cambios de estado y auditoría contractual del asiento.
    """
    asiento = AsientoCuaderno.query.get(id)
    if not asiento:
        return jsonify({'success': False, 'error': 'Asiento no encontrado'}), 404

    historial = HistorialCambio.query.filter_by(id_asiento=id).order_by(HistorialCambio.fecha.asc()).all()
    return jsonify({
        'success': True,
        'id_asiento': id,
        'historial': [h.to_dict() for h in historial]
    }), 200


@asientos_bp.route('/verificar/<string:codigo_qr>', methods=['GET'])
def verificar_codigo_qr(codigo_qr):
    """
    GET /asientos/verificar/<codigo_qr>
    Endpoint público de verificación y auditoría:
    Valida la autenticidad e inalterabilidad del asiento escaneado desde el código QR.
    """
    asiento = AsientoCuaderno.query.filter_by(codigo_qr_verificacion=codigo_qr).first()
    if not asiento:
        return jsonify({
            'success': False,
            'valido': False,
            'error': 'Código QR no reconocido o no registrado en el Cuaderno de Obra oficial'
        }), 404

    return jsonify({
        'success': True,
        'valido': True,
        'mensaje': 'Documento digital oficial certificado e inalterable',
        'asiento': asiento.to_dict(include_details=True),
        'verificado_en': datetime.utcnow().isoformat()
    }), 200
