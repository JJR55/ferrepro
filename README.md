# FerrePro — Sistema de Inventario

## 📊 Descripción General

FerrePro es una **aplicación web de gestión de inventario para ferreterías** con categorización por departamentos (Repuesto, Ferretería, Plomería, Electricidad, Hogar). Diseñada para control completo de:

- 📦 Inventario (costo y precio de venta)
- 🏭 Proveedores
- 🧾 Cuentas por pagar
- 💰 Márgenes de ganancia y rentabilidad
- 🔐 Autenticación y seguridad

---

## 🗄️ Base de Datos: SQLite en localStorage

### ¿Los datos se guardan en SQLite?

**SÍ, pero con una consideración importante:**

- La app usa **sql.js**, que es una implementación de SQLite compilada a WebAssembly
- Los datos se almacenan en **localStorage del navegador**, no en un servidor
- Se exportan/importan automáticamente como strings base64 en localStorage

### Ventajas
✅ Sin servidor requerido  
✅ Funcionamiento completamente offline  
✅ Datos locales, sin envío a internet  
✅ Portabilidad: exportar/importar backup fácilmente  

### Limitaciones
⚠️ Datos solo en el navegador (no sincroniza entre dispositivos)  
⚠️ localStorage tiene límite (~5-10MB por dominio)  
⚠️ Si se borra localStorage, se pierden los datos  

---

## 💾 Backup Automático en localStorage

La app realiza **backups automáticos** cada vez que se guardan cambios:

```javascript
// Se almacenan los últimos 10 backups con timestamp
ferrepro_backups = [
  { timestamp: "2026-05-27T14:30:00Z", size: 125000 },
  { timestamp: "2026-05-27T14:25:00Z", size: 124500 },
  // ... más backups
]
```

### Acceso a backups
Los backups se pueden consultar desde la consola del navegador:
```javascript
JSON.parse(localStorage.getItem('ferrepro_backups'))
```

---

## 🔐 Seguridad - Cambio de Contraseña

### Contraseña por defecto
- **Usuario:** `admin`
- **Contraseña inicial:** `ferrepro2026`

### Cambiar contraseña desde la app
1. Click en botón **🔐 Contraseña** en la barra superior
2. Ingresar contraseña actual
3. Ingresar y confirmar nueva contraseña
4. La nueva contraseña se guarda en `localStorage` automáticamente

```javascript
// Se almacena en localStorage como:
localStorage.setItem('ferrepro_pass', nuevaContrasena)
```

---

## 🎯 Funcionalidades Principales

### Dashboard
- **6 estadísticas en vivo:**
  - Total de artículos
  - Costo total del inventario
  - Valor total de venta
  - **Margen bruto** (ganancia en $ y %)
  - Cantidad de proveedores
  - Facturas pendientes

- **Gráfico de artículos por departamento**
- **Próximos vencimientos de facturas** con alertas

### Inventario
- Crear/editar/eliminar artículos
- Precios de costo y venta separados
- Cálculo automático de totales
- Importar desde Excel
- Exportar a Excel
- **PDF de stock bajo por departamentos** (organizado)

### Proveedores
- Gestión completa de proveedores
- Datos de contacto y RNC
- Enlace con facturas

### Cuentas por Pagar
- Registro de facturas
- Alertas de vencimiento
- Estados: Pendiente, Pagada, Vencida
- PDF de facturas

---

## 📤 Deployment en Vercel

### ¿Por qué Vercel?
✅ Deploy automático desde GitHub  
✅ Hosting gratuito  
✅ Sin necesidad de backend  
✅ Perfect para apps estáticas HTML/JS  
✅ Soporte a Custom Domains  

### Pasos para desplegar

#### 1. Subir a GitHub
```bash
git init
git add .
git commit -m "Inicial FerrePro inventory"
git branch -M main
git remote add origin https://github.com/tuusuario/ferrepro-inventory.git
git push -u origin main
```

#### 2. Desplegar en Vercel
1. Ir a https://vercel.com
2. Hacer login con GitHub
3. Importar repositorio
4. Click en "Deploy"
5. **Listo** — estará disponible en `ferrepro-inventory.vercel.app`

#### 3. Configurar dominio personalizado (opcional)
- En Vercel Dashboard → Settings → Domains
- Agregar tu dominio personalizado
- Configurar DNS según las instrucciones

---

## 📊 Estructura de Datos

### Tabla: `articulos`
```sql
CREATE TABLE articulos (
  id INTEGER PRIMARY KEY,
  codigo TEXT UNIQUE,
  nombre TEXT,
  departamento TEXT,
  precio_costo REAL,
  precio_venta REAL,
  stock INTEGER,
  stock_min INTEGER,
  descripcion TEXT,
  proveedor_id INTEGER,
  unidad TEXT
)
```

### Tabla: `proveedores`
```sql
CREATE TABLE proveedores (
  id INTEGER PRIMARY KEY,
  empresa TEXT,
  contacto TEXT,
  telefono TEXT,
  email TEXT,
  departamento TEXT,
  direccion TEXT,
  rnc TEXT,
  dias_credito INTEGER,
  notas TEXT
)
```

### Tabla: `facturas`
```sql
CREATE TABLE facturas (
  id INTEGER PRIMARY KEY,
  numero TEXT,
  proveedor_id INTEGER,
  monto REAL,
  fecha_emision TEXT,
  fecha_vencimiento TEXT,
  estado TEXT,
  descripcion TEXT
)
```

---

## 📋 Columnas de Inventario

| Campo | Descripción |
|-------|-------------|
| **Código** | Identificador único (SKU) |
| **Nombre** | Nombre del producto |
| **Departamento** | Repuesto, Ferretería, Plomería, Electricidad, Hogar |
| **Precio Costo** | Costo de compra unitario |
| **Total Costo** | Precio Costo × Stock |
| **Precio Venta** | Precio de venta unitario |
| **Total Venta** | Precio Venta × Stock |
| **Stock** | Cantidad disponible |
| **Stock Mín.** | Cantidad mínima antes de alerta |

---

## 🚀 Características de Exportación

### Excel
- Exportar todo el inventario
- Importar desde Excel con validación
- Descargar plantilla de ejemplo

### PDF
- **Stock bajo por departamentos** (tablas separadas)
- **Facturas por pagar** (con alertas de vencimiento)
- Cálculos automáticos de subtotales

---

## 🔄 Flujo de Backup y Sincronización

```
Cambio en Inventario
         ↓
    saveDB()
         ↓
Exportar SQLite a base64
         ↓
Guardar en localStorage['ferrepro_db']
         ↓
Guardar backup en ferrepro_backups[]
         ↓
✅ Datos persistidos
```

---

## ⚙️ Configuración Recomendada

### Para máxima seguridad
1. Cambiar contraseña inicial inmediatamente
2. Guardar regularmente backups del localStorage
3. Usar HTTPS en Vercel (incluido por defecto)

### Para sincronizar entre dispositivos
- Exportar/Importar Excel manualmente
- O migrar a backend real (Node.js + PostgreSQL)

---

## 🛠️ Próximas mejoras sugeridas

- Backend con Node.js + Express para sincronización
- PostgreSQL para datos en servidor
- Usuarios múltiples con roles
- Historial de cambios y auditoría
- API REST para integración con otros sistemas

---

## 📧 Soporte

Para reportar bugs o sugerencias, abrir issue en GitHub.

---

**FerrePro v1.0** — Desenvolvido con ❤️ en 2026
