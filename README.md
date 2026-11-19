# Aplicación Web para la Mejora del Sistema de Gestión de Calidad (SGC)

## 1. Descripción del Proyecto y Problemática

El **Sistema Web de Gestión de Calidad (SGC)** es un prototipo tecnológico desarrollado para optimizar, estandarizar y controlar el ciclo de vida de la información documentada dentro de la Institución.

### Problemática y Alineación Normativa

En la gestión tradicional del SGC, las organizaciones enfrentan frecuentes errores manuales, reprocesos en la redacción de procedimientos y problemas críticos de vigencia documental debido al uso de archivos desactualizados. Para mitigar estas brechas, el sistema asegura el cumplimiento estricto del **numeral 7.5 (Información documentada) de la norma ISO 9001:2015**, garantizando:

* La adecuada creación y actualización de los documentos.

* Su correcta revisión y aprobación mediante una estructura formal.

* La disponibilidad, control de acceso y protección de la vigencia en los puntos de uso.

## 2. Funcionalidades y Módulos del Sistema

La arquitectura funcional de la aplicación se divide en seis módulos principales diseñados para cubrir integralmente la operación del SGC:

1. **Módulo de Autenticación y Perfiles:** Control de acceso seguro basado en credenciales institucionales y asignación de interfaces dinámicas según el rol del usuario.

2. **Módulo Listado Maestro de Documentos:** Inventario centralizado con operaciones CRUD completas, búsqueda individual avanzada, control de versionamiento e importación masiva de datos mediante archivos en formato **Microsoft Excel**.

3. **Módulo de Generación de Procedimientos:** Formulario guiado estructurado con campos obligatorios para asegurar que cada procedimiento cumpla con la plantilla institucional (objetivo, alcance, descripción de actividades, versión y matrices de aprobación).

4. **Módulo de Gestión de Nomenclaturas:** Administración centralizada de las reglas de codificación y secuencias numéricas por tipo de documento, proceso y subproceso.

5. **Módulo de Estilos e Inteligencia Artificial:** Motor de automatización en **Python** asistido por un **agente de Inteligencia Artificial** para parafrasear, formatear y reestructurar borradores antiguos hacia la identidad visual y normativa oficial.

6. **Módulo de Indicadores (Power BI):** Cuadro de mando integrado para la visualización del estado de vigencia, vencimientos temporales y análisis analítico por macroproceso.

## 3. Roles y Control de Acceso (RBAC)

El sistema implementa un modelo de control de acceso basado en roles (*Role-Based Access Control* - RBAC) para garantizar la seguridad de la información documentada y evitar la sobreasignación de privilegios:

| Rol de Usuario | Código de Permiso | Responsabilidades y Alcance en el Sistema | 
| ----- | ----- | ----- | 
| **Administrador** | Global | Acceso total al sistema. Gestiona el Listado Maestro (crear, editar, eliminar), ejecuta cargas masivas mediante Excel, y configura nomenclaturas, reglas de negocio, estilos y parámetros del agente de IA. | 
| **Funcionario / Editor** | `RW` (Lectura y Escritura) | Acceso a los formularios guiados y herramientas de redacción para la elaboración y actualización de procedimientos y documentos del SGC. | 
| **Usuario de Consulta** | `R` (Solo Lectura) | Acceso restringido exclusivamente a la visualización y consulta de documentos vigentes dentro del repositorio institucional, sin permisos de modificación. | 

## 4. Reglas de Negocio y Estandarización Documental

Para mantener la integridad y estandarización del SGC, el sistema aplica rigurosas reglas operativas:

### Regla de Codificación Obligatoria

Todo documento generado en el sistema debe seguir de manera estricta la siguiente secuencia alfanumérica:

$$
\text{[TipoDocumento]}-\text{[Proceso]}-\text{[Subproceso]}-\text{[Consecutivo]}
$$

* **Ejemplo práctico:** `PR-AS-E-001` (Procedimiento - Área Administrativa/Apoyo - Estándar - Consecutivo 001).

### Estructura Mínima Exigida en Procedimientos

Los documentos de tipo procedimiento deben integrar obligatoriamente:

* Encabezado institucional normalizado con código y versión vigente.

* Tabla de elaboración, revisión y aprobación.

* Cuerpo estructurado (Objetivo, Alcance, Descripción detallada de actividades).

* Historial de control de cambios.

* Pie de página institucional.

## 5. Arquitectura y Stack Tecnológico

El desarrollo del prototipo se apoya en un conjunto heterogéneo de tecnologías orientadas a la automatización, la gestión de datos y la inteligencia de negocios:

* **Lenguajes y Lógica Backend:** `Python` para la automatización de procesos, normalización de documentos y soporte lógico de la IA.

* **Entorno de Desarrollo:** `Google Antigravity` (IDE basado en agentes y metodología de *Vibe Coding* e Ingeniería de Instrucciones).

* **Asistencia Inteligente:** Agente de Inteligencia Artificial integrado para la asistencia en la redacción y estructuración normativa.

* **Base de Datos y Almacenamiento:** Base de datos relacional `SQL` para el almacenamiento estructurado del Listado Maestro *(motor específico pendiente de definición en DDL final)*.

* **Visualización e Inteligencia de Negocios:** `Microsoft Power BI` para la analítica de vigencias y tableros de control gerencial.

## 6. Modelo de Datos (Esquema ERD)

El modelo relacional subyacente está compuesto por seis entidades principales con relaciones de tipo $1:N$:

1. **`lista_documentos`**: Tabla central del Listado Maestro. Almacena identidad, título, versión, estado de vigencia y metadatos de los documentos.

2. **`lista_formatos`**: Almacena estructuras, metadatos y registros específicos de las plantillas institucionales.

3. **`tipos_documento`**: Catálogo maestro de clasificaciones (Procedimientos, Instructivos, Formatos, etc.).

4. **`procesos`**: Tabla maestra de macroprocesos institucionales (Estratégicos, Misionales, de Apoyo, Calidad).

5. **`subprocesos`**: Clasificación específica vinculada a cada proceso organizacional.

6. **`usuarios` / `perfiles`**: Registro de usuarios y asignación de permisos según la matriz RBAC.

### Relaciones Clave (Foreign Keys)

* `procesos` (1) $\rightarrow$ `subprocesos` ($N$)

* `tipos_documento` (1) $\rightarrow$ `lista_documentos` ($N$)

* `subprocesos` (1) $\rightarrow$ `lista_documentos` ($N$)

## 7. Flujos de Trabajo Principales

1. **Elaboración Guiada:** El usuario inicia una solicitud; el sistema asigna el código estandarizado (`[TipoDocumento]-[Proceso]-[Subproceso]-[Consecutivo]`) y despliega el formulario estructurado.

2. **Normalización por IA:** Los borradores o archivos antiguos se procesan mediante scripts en Python y el agente de IA para adecuarlos a la identidad visual del SGC.

3. **Control de Cambios y Publicación:** Tras la aprobación, la información se actualiza de forma inmediata en el Listado Maestro.

4. **Monitoreo Temporal:** Power BI consume los datos del sistema para reflejar alertas de vencimiento y el estado actual de la vigencia documental.

## 8. Estado Actual y Hoja de Ruta (Roadmap)

Este repositorio corresponde a la **memoria técnica y prototipo funcional** validado en el marco de un proyecto de grado. Al no incluir manifiestos crudos de dependencias (`package.json` / `requirements.txt`), variables de entorno (`.env`) ni scripts CLI explícitos en esta fase conceptual, se establecen las siguientes recomendaciones técnicas para llevar el prototipo a un entorno de producción:

1. **Definición de Base de Datos (DDL):** Consolidar los esquemas relacionales finales en motores como PostgreSQL o MySQL garantizando las llaves foráneas descritas en el ERD.

2. **Manifiestos y Dependencias:** Configurar los archivos de dependencias (`requirements.txt` para Python / `package.json` para Node.js según corresponda).

3. **Variables de Entorno:** Centralizar credenciales sensibles (como `DATABASE_URL`, claves de API de la IA y `SHAREPOINT_SITE_ID`) en un archivo seguro `.env`.

4. **Modularización del Código:** Estructurar formalmente las carpetas de controladores, modelos y rutas en un entorno MVC o de servicios desacoplados.
