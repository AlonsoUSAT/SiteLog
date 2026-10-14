import os
from flask import Flask, jsonify
from config import config_by_name
from app.extensions import db, jwt, cors

def create_app(config_name=None):
    """
    Fábrica de aplicaciones (Application Factory Pattern).
    Permite instanciar la app Flask configurada según el entorno (desarrollo, testing o producción).
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Asegurar existencia de directorio de subida de evidencias
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # Configuración de respuestas JWT en caso de error
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({
            'success': False,
            'error': 'Falta el encabezado Authorization con formato Bearer <token>'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({
            'success': False,
            'error': 'Token JWT inválido o corrupto'
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'error': 'El token JWT ha expirado. Inicie sesión nuevamente.'
        }), 401

    # Registrar Blueprints
    from app.routes import (
        auth_bp,
        obras_bp,
        asientos_bp,
        incidencias_bp,
        supervision_bp,
        usuarios_bp
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(obras_bp)
    app.register_blueprint(asientos_bp)
    app.register_blueprint(incidencias_bp)
    app.register_blueprint(supervision_bp)
    app.register_blueprint(usuarios_bp)

    # Ruta raíz informativa
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'success': True,
            'app': 'SiteLog - Cuaderno de Obra Digital API REST',
            'version': '2.0.0',
            'estado': 'Servidor operativo',
            'health_check': '/api/health'
        }), 200

    # Endpoint de verificación de estado (Health Check)
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'app': 'SiteLog REST API',
            'version': '1.0.0',
            'environment': config_name
        }), 200

    # Manejo explícito de errores HTTP en JSON
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'success': False, 'error': 'Petición inválida (Bad Request)'}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 'Recurso no encontrado'}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'success': False, 'error': 'Método HTTP no permitido'}), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

    return app
