# Graphify para Restaurant Management

Graphify se usa en Restaurant Management como un mapa estructural local y de solo lectura para orientar el analisis de codigo, dependencias e impacto. No reemplaza OpenSpec, Repomix ni la revision directa del codigo fuente.

## Alcance

Ejecutar Graphify solo desde la raiz versionada de la app:

```bash
cd /home/erpnext/frappe-bench/apps/restaurant_management
```

No ejecutar Graphify desde la raiz de `/home/erpnext/frappe-bench` ni mezclar esta app con otras aplicaciones en el mismo grafo.

Los artefactos locales esperados se ubican en `graphify-out/`. Incluyen `graph.json`, que permite las consultas, y opcionalmente `GRAPH_REPORT.md` y `graph.html`. Estos archivos no son fuente de verdad ni deben versionarse sin autorizacion explicita.

## Flujo de trabajo

1. Revisar Git y OpenSpec antes de cualquier cambio funcional.
2. Consultar Graphify para identificar archivos, dependencias y posibles rutas afectadas.
3. Verificar cada hallazgo importante en el codigo, `hooks.py`, DocTypes, fixtures y configuracion real.
4. Implementar solo el alcance aprobado en OpenSpec y la rama de trabajo.
5. Actualizar el grafo si el cambio altera la estructura de codigo o sus dependencias.
6. Usar Repomix solo cuando sea necesario compartir un contexto Markdown acotado.

## Instalacion local

Graphify y su servidor MCP se instalan como una herramienta aislada con `uv`, fuera de las dependencias Python de Restaurant Management y del entorno de Frappe:

```bash
uv tool install 'graphifyy[mcp]'
```

La instalacion de esta instancia usa:

```text
/home/erpnext/.local/share/uv/tools/graphifyy/
```

No ejecutar `graphify install`, `graphify codex install` ni `uv tool update-shell`. Restaurant Management utiliza las rutas absolutas del entorno aislado y no requiere modificar el `PATH`.

El grafo local se genera desde la raiz de Restaurant Management, solo con analisis AST de codigo:

```bash
cd /home/erpnext/frappe-bench/apps/restaurant_management
GRAPHIFY_QUERY_LOG_DISABLE=1 \
  /home/erpnext/.local/share/uv/tools/graphifyy/bin/graphify \
  extract . --code-only
```

No retirar `--code-only`: evita enviar documentos, imagenes u otros archivos a proveedores de IA y no requiere credenciales.

## Seguridad

Antes de generar el primer grafo, debe existir una `.graphifyignore` que excluya secretos, archivos de entorno, `sites/`, directorios privados, archivos de clientes, logs, respaldos, dumps, certificados, claves, caches y artefactos generados.

No habilitar analisis de PDFs, imagenes, video, URLs, Google Workspace, bases de datos vivas, Pull Requests ni proveedores remotos de IA sin autorizacion explicita. Deshabilitar el registro de consultas con `GRAPHIFY_QUERY_LOG_DISABLE=1`.

## Integracion con Codex

La integracion MCP es opcional y debe configurarse manualmente, por `stdio`, para el archivo `graphify-out/graph.json` de Restaurant Management. No usar `graphify install`, `graphify codex install`, `graphify hook install`, modo estricto, hooks automaticos ni servidores HTTP compartidos.

La configuracion exclusiva del proyecto se encuentra en:

```text
.codex/config.toml
```

El servidor `restaurant_management_graphify` ejecuta `graphify-mcp` por `stdio`, fija el directorio de trabajo en `apps/restaurant_management`, deshabilita el log de consultas y limita las herramientas a lectura local del grafo. Las herramientas de Pull Requests quedan fuera de la lista habilitada para evitar consultas remotas.

Codex carga esta configuracion solo cuando Restaurant Management es un proyecto confiable. Hay que reiniciar o abrir una nueva sesion de Codex desde `apps/restaurant_management` despues de generar el grafo.

Antes de instalar Graphify, crear una configuracion MCP o generar un grafo, solicitar autorizacion explicita. Graphify debe orientar la exploracion; nunca debe modificar codigo, configuracion, datos, DocTypes, fixtures, patches, hooks, permisos, dependencias ni scripts operativos.

## Actualización autorizada del 2026-11-13

Se regeneró el grafo del checkout de desarrollo a partir de la fuente ejecutable
8138a20, conservando un respaldo local en `graphify-out/pre-refresh-20261113-aPtfv3/`.
El directorio de salida sigue ignorado por Git: no se incorpora al repositorio.

La herramienta ya instalada soporta reconstrucción completa de AST sin LLM y
reporte/vista local sin etiquetado por IA:

```bash
GRAPHIFY_QUERY_LOG_DISABLE=1 /home/erpnext/.local/share/uv/tools/graphifyy/bin/graphify extract . --code-only --force --max-workers 2
GRAPHIFY_QUERY_LOG_DISABLE=1 /home/erpnext/.local/share/uv/tools/graphifyy/bin/graphify cluster-only . --no-label
```

Ejecutar desde la raíz de esta app, únicamente con autorización para regenerar.
`--force` aquí fuerza el rescaneo del grafo local; no es un push Git ni modifica
la fuente. No usar `label`, proveedores remotos, extracción de BD, `--global`,
instaladores ni hooks. `--no-label` no genera nuevos nombres mediante LLM; puede
reutilizar etiquetas locales cuya firma coincida y nombrar otras por su nodo hub.

El análisis AST no interpreta todas las relaciones dinámicas de Frappe: esta
ejecución detectó 75 archivos sin nodos (principalmente JSON y módulos vacíos).
Los DocTypes, fixtures y hooks siempre requieren contrastar las fuentes. No
presentar el grafo como una certificación de permisos, stock o contabilidad.
El detalle del resultado y sus límites está en [estado del conocimiento](project-knowledge.md).

### Publicación documental en version-16

El grafo descrito corresponde al checkout instalado con cotización de carrito
candidata; el hash final de esa revisión documental local es ccdf75a. Esta
publicación no incorpora dicho código a version-16, no copia el grafo a otro
checkout y no lo presenta como grafo de mantenimiento. Los artefactos siguen
locales e ignorados; el nuevo commit de documentación no cambia el código
instalado ni invalida el grafo de ese checkout.
