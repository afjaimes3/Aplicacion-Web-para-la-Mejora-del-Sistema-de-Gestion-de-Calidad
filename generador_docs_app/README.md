# Generador de Documentos Institucionales con IA

Esta aplicación es una solución web empresarial diseñada para la creación, gestión, estandarización y automatización de documentos institucionales (Procedimientos, Instructivos, Formatos y Documentos Institucionales) mediante el uso de Inteligencia Artificial (Google Gemini) y plantillas dinámicas de Microsoft Word.

---

## Características Principales

- **Generación Dinámica de Documentos**: Genera documentos en formato `.docx` manteniendo la estructura, encabezados, tablas dinámicas y estilos exactos requeridos por sistemas de gestión de calidad (SGC / ISO 9001).
- **Asistente de Inteligencia Artificial (Google Gemini)**:
  - Redacción y corrección formal de objetivos, alcances y definiciones.
  - Análisis, consistencia y deducción de registros en tablas de actividades.
  - Validación de coherencia en documentos relacionados basada en maestros institucionales.
  - **Administración de Prompts**: Panel administrativo para ajustar prompts del sistema e instrucciones específicas por tipo de documento y sección.
  - Interruptor global y por sección para habilitar/deshabilitar la IA.
- **Gestión de Maestros de Datos**: 
  - Catálogo de procesos, subprocesos y tipos de documentos.
  - Registro de formatos y documentos maestros (fechas de caducidad, versiones, URLs).
  - Carga y descarga masiva mediante plantillas Excel (`.xlsx`).
- **Herramienta de Estandarización de Estilos**:
  - Homogenización de fuentes, tamaños, márgenes y colores institucionales para documentos existentes.
- **Seguridad y Control de Acceso**:
  - Autenticación con contraseñas encriptadas mediante hashes criptográficos seguros (`scrypt`).
  - Roles de acceso diferenciados: Administrador y Usuario.
  - API de solo lectura protegida por token/API Key para integración con herramientas de analítica y BI (ej. Microsoft Power BI).

---

## Tecnologías Utilizadas

- **Backend**: Python 3 con Flask.
- **Base de Datos**: SQLite (almacenamiento liviano, portable y embebido).
- **IA**: Google Gemini API (`gemini-1.5-flash`).
- **Procesamiento de Documentos**: `docx-mailmerge`, `python-docx` y `lxml`.
- **Hojas de Cálculo**: `pandas` y `openpyxl`.
- **Frontend**: HTML5, CSS3 moderno (diseño responsive), JavaScript vanilla y Font Awesome.

---

## Requisitos Previos

- Python 3.10 o superior instalado.
- Opcional: Clave de API de Google Gemini (para funciones de asistencia inteligente).

---

## Instalación y Configuración

1. **Clonar o descargar el repositorio**:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd generador_docs_app
   ```

2. **Crear y activar un entorno virtual**:
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux / macOS:
   source .venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Copie el archivo de ejemplo `.env.example` y renómbrelo a `.env`:
   ```bash
   copy .env.example .env
   ```
   Edite el archivo `.env` para configurar sus claves:
   ```env
   SECRET_KEY=clave_secreta_para_flask_cambiar_en_produccion
   POWERBI_API_KEY=tu_clave_secreta_para_power_bi
   AI_API_KEY=tu_api_key_de_gemini_aqui
   AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent
   AI_MODEL=gemini-1.5-flash
   ```

5. **Inicializar la Base de Datos**:
   El proyecto incluye una base de datos limpia de demostración (`database.db`). Si desea reiniciarla desde cero con datos limpios de ejemplo:
   ```bash
   python init_db.py
   ```

---

## Usuarios de Demostración

La base de datos viene precargada con dos usuarios listos para pruebas:

| Usuario | Contraseña | Rol | Descripción |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | Administrador | Acceso total a maestros, usuarios, prompts de IA y estilos |
| `usuario` | `user123` | Usuario | Creación, edición y generación de documentos institucionales |

---

## Ejecución de la Aplicación

### Opción A (Rápida en Windows):
Haga doble clic en el archivo `START_APP.bat`. Este script verifica el entorno, instala dependencias si es necesario e inicia el servidor.

### Opción B (Línea de Comandos):
```bash
python main.py
```

Abra su navegador web en:
```
http://127.0.0.1:5000
```

---

## Estructura del Proyecto

```
generador_docs_app/
│
├── main.py                     # Punto de entrada de la aplicación Flask
├── auth.py                     # Autenticación, control de sesiones y decoradores de rol
├── document_app.py             # Formulario de documentos, integración IA y exportación Word
├── maestros.py                 # Módulo de administración de maestros (Excel, formatos, docs)
├── admin.py                    # Gestión de usuarios y nomenclaturas
├── admin_ia.py                 # Panel de configuración de prompts y switches de IA
├── api_bi.py                   # API REST de solo lectura protegida para Power BI
├── standardizer_tool.py        # Herramienta de estandarización visual de documentos
├── init_db.py                  # Script para crear e inicializar la base de datos limpia
├── db.py                       # Conexión centralizada a SQLite
│
├── static/                     # Archivos estáticos (CSS, JS, imágenes)
│   ├── css/style.css
│   ├── js/main.js
│   └── img/logo.svg            # Logo institucional genérico
│
├── templates/                  # Plantillas Jinja2 organizadas por módulos
│   ├── base.html
│   ├── document_form.html
│   ├── preview.html
│   ├── admin/
│   ├── auth/
│   ├── menu/
│   └── plantillas/
│
├── plantillas_descargas/       # Plantillas Word oficiales descargables por usuarios
├── utils/                      # Formateadores avanzados de documentos Word
├── requirements.txt            # Dependencias del proyecto
├── .env.example                # Plantilla de variables de entorno segura
└── README.md                   # Documentación del proyecto
```

---

## Licencia

Este proyecto se distribuye bajo fines académicos y demostrativos.
