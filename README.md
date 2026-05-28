# FerrePro — Sistema de Inventario

## 📊 Descripción General

FerrePro es una **aplicación web de gestión de inventario para ferreterías** con categorización por departamentos. Diseñada para control completo de:

- 📦 Inventario (costo y precio de venta)
- 🏭 Proveedores
- 🧾 Cuentas por pagar
- 💰 Márgenes de ganancia y rentabilidad
- 🔐 Autenticación y seguridad
- 💾 Backups en la nube (Turso)
---
---

## 🏗️ Arquitectura

```
Frontend (HTML/CSS/JS)  ───►  API REST (Flask)  ───►  Turso DB (SQLite Cloud)

   index.html                       /api/*                libsql-client
```

<<<<<<< HEAD
- **Frontend**: HTML + CSS + JavaScript puro (sin frameworks)
- **Backend**: Flask Python desplegado como serverless functions en Vercel
- **Base de datos**: Turso (SQLite en la nube, basado en libsql)
=======
### Acceso a backups
Los backups se pueden consultar desde la consola del navegador:
```javascript
JSON.parse(localStorage.getItem('ferrepro_backups'))
```

---

## 🔐 Seguridad - Cambio de Contraseña

### Contraseña por defecto
- **Usuario:** `admin`
- **Contraseña inicial:** ``

### Cambiar contraseña desde la app
1. Click en botón **🔐 Contraseña** en la barra superior
2. Ingresar contraseña actual
3. Ingresar y confirmar nueva contraseña
4. La nueva contraseña se guarda en `localStorage` automáticamente

```javascript
// Se almacena en localStorage como:
localStorage.setItem('ferrepro_pass', nuevaContrasena)
```
>>>>>>> bc6d7c30e7881cb6b94be3eb0678c6ac71259953

---

## 🎯 Funcionalidades Principales

### Dashboard
- **6 estadísticas en vivo:** artículos, costos, ventas, márgenes, proveedores, facturas pendientes
- **Gráfico de artículos por departamento**
- **Próximos vencimientos de facturas** con alertas

### Inventario
- CRUD completo de artículos
- Precios de costo y venta separados con cálculo automático de totales
- Importar/Exportar Excel
- **PDF de stock bajo por departamentos** con subtotales

### Proveedores
- Gestión completa con datos de contacto, RNC y crédito
- Enlace automático con facturas

### Cuentas por Pagar
- Registro de facturas con alertas de vencimiento
- Estados: Pendiente, Pagada, Vencida
- PDF exportable

### 💾 Backups desde la UI
- Crear backups desde el botón en la barra superior
- Listar, descargar y restaurar backups
- **Subir archivos de backup** para restaurar desde el ordenador
- Los backups se almacenan en la nube (Turso) — no en localStorage

---

## 🚀 Deployment en Vercel

### Prerequisitos
1. Cuenta en [Turso](https://turso.tech) (gratis)
2. Cuenta en [Vercel](https://vercel.com) (gratis)
3. Repositorio en GitHub

### Paso 1: Crear base de datos en Turso
```bash
# Instalar CLI de Turso
brew install tursodatabase/tap/turso  # macOS
# O descargar desde https://turso.tech

# Login y crear DB
turso auth login
turso db create ferrepro

# Obtener credenciales
turso db show ferrepro --url        # → TURSO_DATABASE_URL
turso db tokens create ferrepro     # → TURSO_AUTH_TOKEN
```

O puedes crearlo desde el dashboard web de [Turso](https://turso.tech).

### Paso 2: Configurar variables de entorno en Vercel

En Vercel Dashboard → Settings → Environment Variables:

| Variable | Valor |
|----------|-------|
| `TURSO_DATABASE_URL` | `libsql://ferrepro-xxxx.turso.io` |
| `TURSO_AUTH_TOKEN` | Tu token de Turso |
| `ADMIN_PASS` | Contraseña de admin (opcional, default: `ferrepro2026`) |

### Paso 3: Desplegar

```bash
# 1. Subir a GitHub
git add .
git commit -m "FerrePro con backend Flask + Turso"
git push

# 2. En Vercel:
# - Importar repositorio
# - Framework: Other
# - Build: vercel.json ya configurado
# - Click en "Deploy"
```

✅ Listo — tu app estará disponible en `tu-app.vercel.app`

---

## 🛠️ Desarrollo Local

### Backend (Flask)

```bash
# 1. Crear archivo .env con credenciales de Turso
cp .env.example .env
# Editar .env con tus credenciales de Turso

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar servidor
python backend/server.py

# El servidor corre en http://localhost:5000
# La API estará disponible en http://localhost:5000/api/health
```

### Frontend

Abre `index.html` directamente en el navegador, o sirve con:
```bash
python -m http.server 8080
# Abre http://localhost:8080 en el navegador
```

---

## 📡 API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/login` | Login (retorna token) |
| `GET` | `/api/health` | Health check + init DB |
| `GET` | `/api/stats` | Estadísticas del dashboard |
| `GET` | `/api/articulos` | Listar artículos |
| `POST` | `/api/articulos` | Crear artículo |
| `PUT` | `/api/articulos/:id` | Actualizar artículo |
| `DELETE` | `/api/articulos/:id` | Eliminar artículo |
| `GET` | `/api/proveedores` | Listar proveedores |
| `POST` | `/api/proveedores` | Crear proveedor |
| `PUT` | `/api/proveedores/:id` | Actualizar proveedor |
| `DELETE` | `/api/proveedores/:id` | Eliminar proveedor |
| `GET` | `/api/facturas` | Listar facturas |
| `POST` | `/api/facturas` | Crear factura |
| `PUT` | `/api/facturas/:id` | Actualizar factura |
| `DELETE` | `/api/facturas/:id` | Eliminar factura |
| `POST` | `/api/facturas/:id/pagar` | Marcar factura como pagada |
| `GET` | `/api/backups` | Listar backups |
| `POST` | `/api/backups` | Crear backup |
| `POST` | `/api/backups/:id/restore` | Restaurar backup |
| `GET` | `/api/backups/:id/download` | Descargar backup |
| `POST` | `/api/backups/restore-upload` | Restaurar desde archivo subido |
| `DELETE` | `/api/backups/:id` | Eliminar backup |

---

## 📊 Estructura de Datos

```sql
-- Tablas creadas automáticamente por init_db()

CREATE TABLE articulos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo TEXT UNIQUE, nombre TEXT, departamento TEXT,
  precio_costo REAL DEFAULT 0, precio_venta REAL DEFAULT 0,
  stock INTEGER DEFAULT 0, stock_min INTEGER DEFAULT 5,
  descripcion TEXT, proveedor_id INTEGER, unidad TEXT DEFAULT 'u.'
);

CREATE TABLE proveedores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa TEXT, contacto TEXT, telefono TEXT, email TEXT,
  departamento TEXT, direccion TEXT, rnc TEXT,
  dias_credito INTEGER DEFAULT 30, notas TEXT
);

CREATE TABLE facturas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  numero TEXT, proveedor_id INTEGER, monto REAL DEFAULT 0,
  fecha_emision TEXT, fecha_vencimiento TEXT,
  estado TEXT DEFAULT 'pendiente', descripcion TEXT
);

CREATE TABLE backups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT, size INTEGER, created_at TEXT, data TEXT
);
```

---

## 🔐 Seguridad

- **Autenticación**: Bearer token simple
- **Contraseña por defecto**: `ferrepro2026` (configurable via `ADMIN_PASS`)
- **Conexión a Turso**: Autenticada via token
- **Backups**: Almacenados en base64 en la tabla `backups` de Turso

---

## � Estructura del Proyecto

```
ferrepro/
├── index.html          # Frontend (HTML + CSS + JS)
├── api/
│   └── index.py        # Entry point para Vercel
├── backend/
│   ├── __init__.py
│   ├── server.py       # Flask API Server
│   └── db.py           # Conexión a Turso (libsql-client)
├── .env.example        # Variables de entorno de ejemplo
├── requirements.txt    # Dependencias Python
├── vercel.json         # Configuración de Vercel
└── README.md
```

---

## 🛠️ Próximas mejoras sugeridas

- [ ] Autenticación JWT más robusta
- [ ] Historial de cambios y auditoría
- [ ] Roles de usuario (admin, editor, lector)
- [ ] Reportes avanzados (gráficos Chart.js)
- [ ] WebSockets para actualizaciones en tiempo real
- [ ] PWA para uso offline

---

**FerrePro v2.0** — Desenvolvido con ❤️ en 2026  
Backend: Flask + Turso | Frontend: HTML/CSS/JS | Deploy: Vercel