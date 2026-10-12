# 🏗️ SiteLog - API REST Backend (Flask + MySQL + JWT)
> **Sistema móvil para la gestión y trazabilidad del Cuaderno de Obra digital**  
> *Universidad Católica Santo Toribio de Mogrovejo (USAT) — Ciclo VIII — Grupo A — 2026-II*

---

## 📁 Estructura del Proyecto

```text
SiteLog/
├── app/
│   ├── __init__.py           # Application Factory (create_app, Blueprints, Error Handlers)
│   ├── extensions.py         # Instancias desacopladas de SQLAlchemy, JWT y CORS
│   ├── models/               # Modelos SQLAlchemy para MySQL (Sección 7 de la rúbrica)
│   │   ├── __init__.py
│   │   ├── usuario.py        # Tabla usuarios (auth, roles, fcm_token)
│   │   ├── obra.py           # Tabla obras (georreferenciadas con radio de 50m)
│   │   ├── frente.py         # Tabla frentes_obra (hitos/sectores de trabajo)
│   │   ├── asiento.py        # Tabla asientos_cuaderno (correlativo, QR inalterable)
│   │   ├── respuesta.py      # Tabla respuestas_asiento (absoluciones del supervisor)
│   │   ├── incidencia.py     # Tabla incidencias_obra
│   │   ├── evidencia.py      # Tabla evidencias (fotos multipart)
│   │   ├── historial.py      # Tabla historial_cambios (auditoría y trazabilidad)
│   │   └── notificacion.py   # Tabla notificaciones_log (auditoría push FCM)
│   ├── routes/               # Blueprints modulares de la API REST
│   │   ├── __init__.py
│   │   ├── auth.py           # /auth (login, fcm-token)
│   │   ├── obras.py          # /obras (listado, detalle, asientos)
│   │   ├── asientos.py       # /asientos (registro transaccional, QR, respuestas)
│   │   ├── incidencias.py    # /incidencias (actualización de estados)
│   │   ├── supervision.py    # /supervision (KPIs contractuales)
│   │   └── usuarios.py       # /usuarios (residentes activos)
│   └── utils/
│       ├── __init__.py
│       └── decorators.py     # Decorador @role_required para control de acceso
├── config.py                 # Configuración de entornos y URI de MySQL
├── run.py                    # Punto de entrada y comandos CLI (init-db, seed-db)
├── schema.sql                # Script DDL de MySQL para importación directa
├── requirements.txt          # Dependencias de Python
├── .env.example              # Plantilla de variables de entorno
├── .gitignore                # Archivos ignorados en Git (venv, .env, __pycache__)
└── README.md                 # Guía del proyecto y flujo colaborativo de Git
```

---

## 👥 Guía de Trabajo Colaborativo en Git (3 Integrantes)

Para evitar que existan **3 estructuras distintas**, se debe seguir este flujo riguroso:

### Paso 1: El Integrante que Monta la Base (Tú)
1. Abre tu terminal en la carpeta `SiteLog`.
2. Si no tienes Git instalado en tu máquina, instálalo desde [git-scm.com](https://git-scm.com/) o vía GitHub Desktop.
3. Inicializa el repositorio local y realiza el primer commit:
   ```bash
   git init
   git add .
   git commit -m "feat: estructura base de Flask con SQLAlchemy, JWT y MySQL para SiteLog"
   ```
4. Crea un repositorio vacío en **GitHub** o **GitLab** llamado `SiteLog` (o `SiteLog-Backend`).
5. Conéctalo y súbelo a la rama principal:
   ```bash
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/SiteLog.git
   git push -u origin main
   ```
6. Agrega a tus otros 2 compañeros como **Colaboradores** en los Ajustes del repositorio (*Settings > Collaborators*).

---

### Paso 2: Los otros 2 Integrantes (Revisan y Clonan)
1. **NO** crean otra estructura ni inicializan proyectos nuevos desde cero.
2. Clonan el repositorio oficial:
   ```bash
   git clone https://github.com/TU_USUARIO/SiteLog.git
   cd SiteLog
   ```
3. Cada uno crea su propio entorno virtual y su archivo `.env` local (ver instrucciones abajo).
4. Para desarrollar nuevas funcionalidades, cada integrante trabaja en su propia rama:
   ```bash
   git checkout -b feature/modulo-android-login
   # o
   git checkout -b feature/api-sync-workmanager
   ```

---

## ⚙️ Instalación y Puesta en Marcha Local

### 1. Crear y Activar el Entorno Virtual
En Windows (PowerShell o CMD):
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Instalar Dependencias
```powershell
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Copia el archivo `.env.example` y renómbralo a `.env`:
```powershell
copy .env.example .env
```
Edita `.env` con las credenciales de tu servidor MySQL local (por ejemplo, XAMPP, WampServer o MySQL Server):
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_clave_aqui
DB_NAME=sitelog_db
```

### 4. Inicializar la Base de Datos y Cargar Datos de Prueba
Asegúrate de que el servicio MySQL esté corriendo y ejecuta:
```powershell
flask init-db
flask seed-db
```
*(Alternativamente, puedes importar el archivo `schema.sql` directamente desde phpMyAdmin o MySQL Workbench).*

### 5. Iniciar la API REST
```powershell
python run.py
```
La API estará disponible en: `http://localhost:5000`  
Verificación de estado: `http://localhost:5000/api/health`

---

## 🔑 Cuentas de Demostración Semilla

| Rol | Correo | Contraseña | Finalidad en SiteLog |
|---|---|---|---|
| **Administrador** | `admin@sitelog.pe` | `admin123` | Supervisión global, auditoría QR, asignación de profesionales |
| **Residente** | `residente@sitelog.pe` | `residente123` | Registro de asientos, incidencias y fotos en campo (radio 50m) |
| **Supervisor** | `supervisor@sitelog.pe` | `supervisor123` | Absolución formal de consultas, inspección y validación de QR |
