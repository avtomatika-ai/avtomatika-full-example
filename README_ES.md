# Avtomatika: Demostración Completa de Funcionalidades

[EN](./README.md) | ES | [RU](./README_RU.md)

Este proyecto proporciona una demostración exhaustiva del ecosistema **Avtomatika HLN (Hierarchical Logic Network)**. Sirve como el "Gold Standard" para pruebas E2E, cubriendo todos los patrones arquitectónicos y las capacidades avanzadas de los trabajadores (workers).

## 🏗 Arquitectura del Sistema

El ejemplo despliega un entorno distribuido completo:

![Blueprint Principal](docs/images/full_showcase_graph.png)

1.  **Orchestrator**: El motor central que gestiona blueprints complejos con sub-trabajos anidados. Paquete `avtomatika` de PyPI.
2.  **GPU Worker**: Demuestra tareas pesadas con **Informes de Progreso**, **Caché Caliente (Hot Cache)** y **Carga de Archivos a S3**. Paquete `avtomatika-worker` de PyPI.
3.  **CPU Workers**: Dos ejecutores para análisis paralelo (uno confiable, uno inestable para pruebas de reputación).
4.  **Webhook Receiver**: Servicio externo que recibe notificaciones de trabajos en tiempo real.
5.  **Infraestructura**: Redis (estado), PostgreSQL (historial), MinIO (S3), VictoriaMetrics, Grafana y Jaeger.

## 🌟 Escaparate de Características Avanzadas

Este ejemplo demuestra el 100% de la funcionalidad principal de **Avtomatika HLN**:

### 1. Despacho Robusto (Indexación ZSET)
Todo el descubrimiento de trabajadores está impulsado por Redis **Sorted Sets (ZSET)**. Las marcas de tiempo de expiración se utilizan como puntuaciones (scores), lo que permite al orquestador filtrar trabajadores obsoletos de forma atómica. Esto elimina las condiciones de carrera de "datos faltantes".

### 2. Robo de Trabajo (Work Stealing) Confiable
Los trabajadores inactivos pueden "robar" tareas de las colas de los trabajadores ocupados para garantizar la máxima utilización. El sistema garantiza actualizaciones atómicas de `assigned_worker_id`.

### 3. Human-in-the-Loop (Aprobación Humana)
Integración de `actions.await_human_approval()`. El pipeline se pausa al inicio, pasando al estado `waiting_for_human` hasta que se recibe una decisión externa `APPROVED` a través de la API Pública.


### 2. Despacho Inteligente y Consciente de Costos
*   **Restricciones de Recursos**: Tareas que requieren CPU/RAM específicos (usando lógica GE - Mayor o Igual).
*   **Coincidencia de Caché Caliente**: Uso de `resource_hint` para apuntar a trabajadores que ya tienen activos específicos (ej. modelos de IA) precargados.
*   **Límites de Costo**: Restricción de tareas a trabajadores dentro de un rango de `max_cost`.
*   **Tiempos de Espera (Timeouts)**: Control detallado de `dispatch_timeout` y `result_timeout`.

### 3. Interacción Rica con el Trabajador
*   **Progreso en Tiempo Real**: Trabajadores emitiendo `send_progress(0.33, "Procesando...")` visible vía API/WS.
*   **Eventos de Trabajador Personalizados**: Emisión de eventos de negocio o hardware (ej. `gpu_thermal_status`) durante la ejecución de la tarea.
*   **TaskFiles y S3**: Sincronización automática. Si un trabajador devuelve una ruta a un archivo creado vía `TaskFiles`, el SDK lo carga automáticamente a S3.

### 4. Seguridad Zero-Trust
*   Cada mensaje está firmado criptográficamente.
*   El Orchestrator verifica las firmas de todos los actores, incluidos los eventos internos "Ghost" de los Blueprints.
*   Protección contra repetición mediante marcas de tiempo obligatorias.

### 5. Sintaxis de Blueprint Moderna
*   **Enrutamiento Condicional**: Uso de decoradores `.when("condición")` para ramificación declarativa.
*   **Nombres Inferidos**: Los nombres de los estados se derivan automáticamente de los nombres de las funciones.
*   **Paralelismo**: Fácil `fan-out / fan-in` vía `actions.dispatch_parallel()`.

## 🚀 Inicio Rápido

### 1. Lanzar con Docker (Stack Completo)
```bash
docker compose up -d --build
```

### 2. Ejecutar Validación Completa Automatizada
Realiza una auditoría profunda (linting, gráficos, ejecución de escenarios con emulación de aprobación humana, verificación de S3 y métricas):
```bash
make full-check
```

### 3. Cliente de Demostración Interactivo
```bash
make init
.venv/bin/python3 client.py
```

## 📂 Estructura de Archivos

*   `blueprints/main.py`: Flujo complejo con aprobación humana, paralelismo y S3.
*   `blueprints/sub.py`: Sintaxis moderna con condiciones `.when()`.
*   `workers/gpu.py`: Trabajador avanzado con Progreso, Eventos y Caché Caliente.
*   `workers/cpu_*.py`: Trabajadores simples para análisis y pruebas de reputación.

---
*Desarrollado por Dmitrii Gagarin aka madgagarin.*
