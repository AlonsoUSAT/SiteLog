import os
import pymysql
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import (
    Usuario,
    Obra,
    FrenteObra,
    AsientoCuaderno,
    RespuestaAsiento,
    IncidenciaObra,
    Evidencia,
    HistorialCambio,
    NotificacionLog
)

app = create_app(os.getenv('FLASK_ENV', 'development'))


def ensure_database_exists():
    """Crea la base de datos en MySQL si aún no existe antes de ejecutar SQLAlchemy."""
    db_host = app.config.get('DB_HOST', 'localhost')
    db_port = int(app.config.get('DB_PORT', 3306))
    db_user = app.config.get('DB_USER', 'root')
    db_password = app.config.get('DB_PASSWORD', '')
    db_name = app.config.get('DB_NAME', 'sitelog_db')

    connection = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        charset='utf8mb4'
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        connection.commit()
        print(f" [OK] Base de datos '{db_name}' verificada/creada en MySQL ({db_host}:{db_port}).")
    finally:
        connection.close()


@app.cli.command('init-db')
def init_db():
    """Crea la base de datos y las 9 tablas del modelo de datos en MySQL."""
    with app.app_context():
        ensure_database_exists()
        db.create_all()
        print(" [OK] Las 9 tablas de SiteLog fueron creadas exitosamente en MySQL:")
        print("      - usuarios, obras, frentes_obra, asientos_cuaderno, respuestas_asiento,")
        print("      - incidencias_obra, evidencias, historial_cambios, notificaciones_log")


@app.cli.command('seed-db')
def seed_db():
    """Puebla las 9 tablas con datos completos de demostración académica (Sección 7 y 13)."""
    with app.app_context():
        ensure_database_exists()
        db.create_all()

        # 1. TABLA: usuarios (3 roles diferenciados)
        if not Usuario.query.filter_by(correo='admin@sitelog.pe').first():
            admin = Usuario(
                nombre='Ing. Carlos Mendoza (Admin)',
                correo='admin@sitelog.pe',
                rol='Administrador',
                colegiatura='CIP-100234',
                activo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

        if not Usuario.query.filter_by(correo='residente@sitelog.pe').first():
            residente = Usuario(
                nombre='Ing. Alonso Pérez (Residente)',
                correo='residente@sitelog.pe',
                rol='Residente',
                colegiatura='CIP-245890',
                activo=True
            )
            residente.set_password('residente123')
            db.session.add(residente)

        if not Usuario.query.filter_by(correo='supervisor@sitelog.pe').first():
            supervisor = Usuario(
                nombre='Ing. Diana Salazar (Supervisora)',
                correo='supervisor@sitelog.pe',
                rol='Supervisor',
                colegiatura='CIP-189745',
                activo=True
            )
            supervisor.set_password('supervisor123')
            db.session.add(supervisor)

        db.session.commit()

        u_res = Usuario.query.filter_by(correo='residente@sitelog.pe').first()
        u_sup = Usuario.query.filter_by(correo='supervisor@sitelog.pe').first()

        # 2. TABLA: obras (2 obras en estados diferentes) y 3. TABLA: frentes_obra (8 frentes)
        obra1 = Obra.query.filter_by(codigo_contrato='OBRA-2026-CHIC-01').first()
        if not obra1:
            obra1 = Obra(
                codigo_contrato='OBRA-2026-CHIC-01',
                nombre='Mejoramiento de la Transitabilidad Urbana en Av. Balta - Chiclayo',
                ubicacion_lat=-6.77137,
                ubicacion_lon=-79.84088,
                radio_metros=50.0,
                estado='En ejecución',
                id_residente=u_res.id,
                id_supervisor=u_sup.id
            )
            db.session.add(obra1)
            db.session.flush()

            frentes_obra1 = [
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector A: Intersección Av. Bolognesi', latitud=-6.77100, longitud=-79.84050),
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector B: Tramo Plaza Principal', latitud=-6.77140, longitud=-79.84090),
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector C: Tramo Mercado Central', latitud=-6.77180, longitud=-79.84120),
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector D: Cruce Pedro Ruiz', latitud=-6.77220, longitud=-79.84160),
            ]
            db.session.add_all(frentes_obra1)
            db.session.flush()

        obra2 = Obra.query.filter_by(codigo_contrato='OBRA-2026-PIM-02').first()
        if not obra2:
            obra2 = Obra(
                codigo_contrato='OBRA-2026-PIM-02',
                nombre='Construcción del Centro de Salud Nivel I-4 en Pimentel',
                ubicacion_lat=-6.83720,
                ubicacion_lon=-79.93410,
                radio_metros=50.0,
                estado='Con observaciones',
                id_residente=u_res.id,
                id_supervisor=u_sup.id
            )
            db.session.add(obra2)
            db.session.flush()

            frentes_obra2 = [
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 1: Emergencia y Triaje', latitud=-6.83710, longitud=-79.93400),
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 2: Consulta Externa', latitud=-6.83725, longitud=-79.93415),
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 3: Hospitalización y Quirófano', latitud=-6.83740, longitud=-79.93430),
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 4: Subestación Eléctrica y Almacén', latitud=-6.83755, longitud=-79.93445),
            ]
            db.session.add_all(frentes_obra2)
            db.session.flush()

        # 4. TABLA: asientos_cuaderno (4 tipos y varios estados)
        if AsientoCuaderno.query.count() == 0:
            frente_a = FrenteObra.query.filter_by(id_obra=obra1.id).first()
            frente_m1 = FrenteObra.query.filter_by(id_obra=obra2.id).first()

            asiento1 = AsientoCuaderno(
                id_obra=obra1.id,
                id_frente=frente_a.id,
                numero_correlativo=1,
                tipo='Notificación',
                titulo='Apertura del Cuaderno de Obra Digital y Entrega de Terreno',
                descripcion='Se deja constancia del inicio oficial de partidas preliminares en el Sector A con presencia del Residente y Supervisión.',
                lat_registro=-6.77100,
                lon_registro=-79.84050,
                estado='Absuelto',
                codigo_qr_verificacion='SITELOG-OBRA1-AS1-DEMO0001CERT',
                id_usuario=u_res.id
            )
            asiento2 = AsientoCuaderno(
                id_obra=obra1.id,
                id_frente=frente_a.id,
                numero_correlativo=2,
                tipo='Consulta',
                titulo='Consulta sobre interferencia de red de agua potable matriz',
                descripcion='Durante la excavación de subrasante a -1.20m se halló tubería PVC no contemplada en el expediente técnico. Se solicita absolución.',
                lat_registro=-6.77138,
                lon_registro=-79.84089,
                estado='Pendiente de Absolución',
                codigo_qr_verificacion='SITELOG-OBRA1-AS2-DEMO0002CERT',
                id_usuario=u_res.id
            )
            asiento3 = AsientoCuaderno(
                id_obra=obra2.id,
                id_frente=frente_m1.id,
                numero_correlativo=1,
                tipo='Instrucción',
                titulo='Observación al curado de concreto en zapatas del Módulo 1',
                descripcion='La supervisión observa deficiente hidratación en elementos estructurales vaciados el día anterior.',
                lat_registro=-6.83710,
                lon_registro=-79.93400,
                estado='Observado',
                codigo_qr_verificacion='SITELOG-OBRA2-AS1-DEMO0003CERT',
                id_usuario=u_sup.id
            )
            asiento4 = AsientoCuaderno(
                id_obra=obra2.id,
                id_frente=frente_m1.id,
                numero_correlativo=2,
                tipo='Modificación',
                titulo='Solicitud de adicional por mejoramiento de suelo de fundación',
                descripcion='Se registra sustento técnico de ensayo de mecánica de suelos para reemplazo de estrato arcilloso.',
                lat_registro=-6.83725,
                lon_registro=-79.93415,
                estado='Emitido',
                codigo_qr_verificacion='SITELOG-OBRA2-AS2-DEMO0004CERT',
                id_usuario=u_res.id
            )
            db.session.add_all([asiento1, asiento2, asiento3, asiento4])
            db.session.flush()

            # 5. TABLA: respuestas_asiento
            resp1 = RespuestaAsiento(
                id_asiento=asiento1.id,
                id_supervisor=u_sup.id,
                descripcion='Se da por conforme el acta de entrega de terreno y trazo inicial en el Sector A.'
            )
            db.session.add(resp1)

            # 6. TABLA: incidencias_obra (2 incidencias de tipos diferentes)
            inc1 = IncidenciaObra(
                id_asiento=asiento2.id,
                tipo_incidencia='Interferencia de terceros',
                descripcion='Red matriz de EPSEL sin catastro actualizado paraliza excavación en progresiva 0+120.',
                impacto_contractual='Riesgo de ampliación de plazo de 3 días calendario'
            )
            inc2 = IncidenciaObra(
                id_asiento=asiento3.id,
                tipo_incidencia='Vicio oculto',
                descripcion='Afloramiento de napa freática superficial en excavación de cisterna principal.',
                impacto_contractual='Requiere bombeo permanente y aditivo impermeabilizante'
            )
            db.session.add_all([inc1, inc2])
            db.session.flush()

            # 7. TABLA: evidencias
            ev1 = Evidencia(
                id_asiento=asiento2.id,
                id_incidencia=inc1.id,
                ruta_archivo='evidencia_tuberia_sector_a.jpg',
                tipo='IMAGEN'
            )
            db.session.add(ev1)

            # 8. TABLA: historial_cambios
            hist1 = HistorialCambio(
                id_asiento=asiento1.id,
                estado_anterior='Emitido',
                estado_nuevo='Absuelto',
                comentario='Conformidad otorgada por Supervisión en campo.',
                id_usuario=u_sup.id
            )
            hist2 = HistorialCambio(
                id_asiento=asiento2.id,
                estado_anterior=None,
                estado_nuevo='Pendiente de Absolución',
                comentario='Apertura de consulta técnica con plazo contractual.',
                id_usuario=u_res.id
            )
            db.session.add_all([hist1, hist2])

            # 9. TABLA: notificaciones_log
            notif1 = NotificacionLog(
                id_usuario=u_sup.id,
                id_asiento=asiento2.id,
                tipo='NUEVA_CONSULTA',
                mensaje='El Residente ha registrado la Consulta #2 en OBRA-2026-CHIC-01.',
                fcm_result='SENT_DEMO_OK'
            )
            db.session.add(notif1)

        db.session.commit()
        print(" [OK] Datos semilla cargados exitosamente en las 9 tablas de SiteLog.")


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
