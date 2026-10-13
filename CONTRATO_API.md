# 🤝 Contrato Común de la API REST y División de Módulos — SiteLog
> **Equipo:** Alonso, Mia y Dana  
> **Asignatura:** Desarrollo de Aplicaciones Móviles — USAT 2026-II

Para que la integración del equipo y el consumo desde Android (Retrofit + Gson) funcionen sin conflictos, **los 3 bloques deben cumplir estrictamente este contrato técnico**.

---

## 1. División de Endpoints por Integrante (Punto 8)

### 👤 Bloque 1: ALONSO — Autenticación y Obras (5 endpoints)
* **Rama de Git:** `git checkout -b feature/alonso-auth-obras`
* **Archivos:** `app/routes/auth.py` y `app/routes/obras.py`

| # | Método | Endpoint | Rol mínimo | Descripción |
|---|---|---|---|---|
| 1 | `POST` | `/auth/login` | Público | Autentica y devuelve JWT con `id`, `nombre` y `rol`. |
| 2 | `POST` | `/auth/fcm-token` | Autenticado | Registra o actualiza el token FCM del dispositivo. |
| 3 | `GET` | `/obras` | Autenticado | Lista obras según rol. Filtros: `estado`, `residente`. |
| 4 | `GET` | `/obras/{id}` | Autenticado | Detalle general de la obra, frentes y resumen de asientos. |
| 5 | `GET` | `/obras/{id}/asientos` | Autenticado | Lista cronológica de asientos. Filtros: `tipo`, `estado`, `fechas`. |

---

### 👤 Bloque 2: MIA — Asientos del Cuaderno y Verificación QR (6 endpoints)
* **Rama de Git:** `git checkout -b feature/mia-asientos-qr`
* **Archivo:** `app/routes/asientos.py`

| # | Método | Endpoint | Rol mínimo | Descripción |
|---|---|---|---|---|
| 1 | `POST` | `/asientos` | Residente | Registra nuevo asiento con correlativo transaccional, geocerca con accuracy GPS, hash SHA-256 inmutable y QR. |
| 2 | `GET` | `/asientos/{id}` | Autenticado | Detalle del asiento con respuestas, incidencias y evidencias. |
| 3 | `POST` | `/asientos/{id}/responder` | Supervisor | Absolución formal de consulta técnica; transiciona el asiento a `ABSUELTO`. |
| 4 | `PUT` | `/asientos/{id}/estado` | Supervisor / Admin | Transiciones de ciclo de vida oficial (`EMITIDO -> OBSERVADO`, `OBSERVADO -> ABSUELTO`, `ABSUELTO -> CONCLUIDO`). |
| 5 | `GET` | `/asientos/verificar/{codigo_qr}` | Público | Verifica autenticidad e integridad del asiento recalculando hash SHA-256 frente a adulteraciones en BD. |
| 6 | `GET` | `/asientos/{id}/historial` | Autenticado | Trazabilidad cronológica de cambios de estado y objeciones. |

---

### 👤 Bloque 3: DANA — Incidencias, Evidencias y Supervisión (5 endpoints)
* **Rama de Git:** `git checkout -b feature/dana-incidencias-supervision`
* **Archivos:** `app/routes/incidencias.py`, `app/routes/supervision.py`, `app/routes/usuarios.py` (y ruta de incidencias en `asientos.py`)

| # | Método | Endpoint | Rol mínimo | Descripción |
|---|---|---|---|---|
| 1 | `POST` | `/asientos/{id}/incidencias` | Residente | Registra incidencia técnica; admite `multipart/form-data` si incluye foto. |
| 2 | `PUT` | `/incidencias/{id}/estado` | Supervisor | Actualiza estado u observación del Supervisor sobre una incidencia. |
| 3 | `DELETE` | `/incidencias/{id}` | Residente / Sup / Admin | Elimina una incidencia preliminar (bloqueado con 409 si el asiento asociado ya está `CONCLUIDO` o `ABSUELTO`). |
| 4 | `GET` | `/supervision/kpis-contractuales` | Supervisor / Admin | KPIs: obras por estado, consultas pendientes, 5 estados oficiales e incidencias. |
| 5 | `GET` | `/usuarios/residentes` | Supervisor / Admin | Lista residentes activos disponibles para asignación. |

---

## 2. Formato JSON Uniforme (Éxito y Error)

Todas las respuestas deben devolverse con `jsonify({...}), CODIGO_HTTP` e incluir siempre el booleano `"success"`:

### ✅ Respuesta de Éxito (`200 OK` o `201 Created`)
```json
{
  "success": true,
  "message": "Descripción breve opcional",
  "recurso": { ... }
}
```
* **Convención de claves:**
  * Si devuelve **una lista**, usar clave en plural (`"obras": [...]`, `"asientos": [...]`, `"residentes": [...]`, `"historial": [...]`).
  * Si devuelve **un objeto**, usar clave en singular (`"obra": {...}`, `"asiento": {...}`, `"incidencia": {...}`, `"usuario": {...}`).

### ❌ Respuesta de Error (`400`, `401`, `403`, `404`, `409`, `500`)
Siempre usar la clave `"error"` en singular con un mensaje claro para mostrar en la interfaz móvil:
```json
{
  "success": false,
  "error": "Mensaje claro explicando qué falló"
}
```

### 📊 Códigos HTTP Estándar
| Código | Uso obligatorio |
|---|---|
| `200` | Consulta (`GET`) o actualización (`PUT` / absolución) exitosa. |
| `201` | Creación exitosa (`POST /asientos`, `POST /asientos/{id}/incidencias`). |
| `400` | Faltan campos obligatorios en el body o datos inválidos. |
| `401` | Falta token JWT, token expirado o credenciales inválidas. |
| `403` | Token válido, pero el rol del usuario no tiene permiso para esa ruta. |
| `404` | No existe el `id` solicitado o el `codigo_qr` no es válido. |
| `409` | Conflicto o registro duplicado (ej. UUID de operación offline repetido). |
| `500` | Error interno de base de datos (ejecutar siempre `db.session.rollback()`). |

---

## 3. Envío y Lectura del Token JWT

* **Encabezado HTTP en cada petición protegida:**
  ```http
  Authorization: Bearer <token_jwt>
  ```
* **Cómo obtener al usuario autenticado dentro de cualquier ruta:**
  ```python
  from flask_jwt_extended import get_jwt_identity
  from app.utils.decorators import get_current_user

  # Opción 1: Obtener solo el ID (entero)
  user_id = int(get_jwt_identity())

  # Opción 2: Obtener la instancia completa de Usuario (SQLAlchemy)
  usuario = get_current_user()
  ```

---

## 4. Validación de Roles en cada Ruta

* **Nombres exactos de los 3 roles en Base de Datos:**
  * `'Residente'`
  * `'Supervisor'`
  * `'Administrador'`

* **Para rutas que requieren cualquier usuario logueado:**
  ```python
  from flask_jwt_extended import jwt_required

  @obras_bp.route('/<int:id>', methods=['GET'])
  @jwt_required()
  def detalle_obra(id):
      ...
  ```

* **Para rutas que exigen roles específicos (usar `@role_required` de `app/utils/decorators.py`):**
  ```python
  from flask_jwt_extended import jwt_required
  from app.utils.decorators import role_required

  @asientos_bp.route('', methods=['POST'])
  @jwt_required()
  @role_required(['Residente', 'Administrador'])
  def registrar_asiento():
      ...
  ```

---

## 5. Serialización de Modelos
* Usar siempre el método `.to_dict()` ya incluido en todos los modelos de `app/models/` para garantizar que los nombres de campos y fechas (`.isoformat()`) sean idénticos en toda la API.
