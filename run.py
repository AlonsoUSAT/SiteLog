import os
from app import create_app
from app.extensions import db
from app.models import Usuario, Obra, FrenteObra, AsientoCuaderno, IncidenciaObra

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.cli.command('init-db')
def init_db():
    """Crea todas las tablas en la base de datos MySQL."""
    with app.app_context():
        db.create_all()
        print(" [OK] Todas las tablas fueron creadas exitosamente en la base de datos.")


@app.cli.command('seed-db')
def seed_db():
    """Puebla la base de datos con los datos mínimos para la demostración académica (3 roles, 2 obras, 8 frentes)."""
    with app.app_context():
        db.create_all()

        # 1. Crear Usuarios de prueba si no existen
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

        # 2. Crear 2 Obras de demostración si no existen
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

            # 4 Frentes para Obra 1
            frentes_obra1 = [
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector A: Intersección Av. Bolognesi', latitud=-6.77100, longitud=-79.84050),
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector B: Tramo Plaza Principal', latitud=-6.77140, longitud=-79.84090),
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector C: Tramo Mercado Central', latitud=-6.77180, longitud=-79.84120),
                FrenteObra(id_obra=obra1.id, nombre_sector='Sector D: Cruce Pedro Ruiz', latitud=-6.77220, longitud=-79.84160),
            ]
            db.session.add_all(frentes_obra1)

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

            # 4 Frentes para Obra 2
            frentes_obra2 = [
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 1: Emergencia y Triaje', latitud=-6.83710, longitud=-79.93400),
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 2: Consulta Externa', latitud=-6.83725, longitud=-79.93415),
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 3: Hospitalización y Quirófano', latitud=-6.83740, longitud=-79.93430),
                FrenteObra(id_obra=obra2.id, nombre_sector='Módulo 4: Subestación Eléctrica y Almacén', latitud=-6.83755, longitud=-79.93445),
            ]
            db.session.add_all(frentes_obra2)

        db.session.commit()
        print(" [OK] Datos de demostración (3 usuarios, 2 obras y 8 frentes) cargados exitosamente.")


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
