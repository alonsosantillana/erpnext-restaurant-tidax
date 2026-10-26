# Validation and handoff

## Scope verified

- Host local confirmado como 192.168.2.53; repositorio restaurant_management.
- master y upstream/master coincidían en cd6564d al iniciar, árbol limpio.
- Rama local: fix/pedidosya-jwt-auth-hook. No merge ni push en este alcance.
- Solo se cambió código/documentación/pruebas de esta app. No se modificaron
  Frappe, ERPNext, ovenube_peru, silent_print ni resto.v1.tidax.pe.
- No se ejecutaron migrate, restart, clear-cache, bench run-tests, consultas a
  proveedores ni escrituras de configuración o datos operativos.

## Reproduction and results

Antes del cambio fallaban la comprobación de registro del hook y la prueba de JWT
válido: validate_auth real de Frappe lanzaba AuthenticationError antes del endpoint.
Después del arreglo se ejecutó:

```bash
PYTHONDONTWRITEBYTECODE=1 ../../env/bin/python -m unittest discover \
  -s restaurant_management/integrations/pedidosya -p 'test_*.py' -v
```

Resultado: 44 pruebas aprobadas. Incluyen firmas/algoritmos HMAC, exp/servicio,
issuer/audience, leeway 0/predeterminado, configuración y usuario inválidos,
aislamiento de secretos por configuración, rutas/métodos exactos, desvíos cmd y
override, preservación de parámetros y limpieza de permisos mediante set_user
real. Cubren también contratos dispatch 202/200, status 200 y payload inválido
400, más la regresión previa de parsing, idempotencia, rollback y test=true.

La DB es Mock y las consultas solo admiten Settings/User esperados; frappe.connect
está bloqueado en la suite nueva. No se inicializa sitio. Las pruebas usan los
validate_auth y set_user de Frappe reales, pero simulan OAuth, API keys, validación
IP, persistencia y colas. No prueban WSGI/init_request completo ni una BD real.

- AST de 13 archivos Python correcto, sin generar bytecode.
- git diff --check correcto.
- OpenSpec estricto válido con Node.js 20.20.2, sin cambiar runtime global.
- Revisión especializada de integración/autenticación: sin bloqueantes.
- Graphify regenerado completo con --code-only --no-cluster --force y después
  cluster-only --no-label. El modo incremental había producido un grafo parcial;
  la reconstrucción completa lo reemplazó, conservando respaldos locales.
  Resultado final: 2350 nodos, 4316 relaciones, 254 comunidades. Artefactos ignorados
  por Git, sin proveedores de IA ni instalación de hooks automáticos.

## Pending operational validation

La corrección está en el código de desarrollo, no desplegada en el servidor de
pruebas remoto. Para una publicación/despliegue posterior se requiere autorización.
No necesita migrate ni build de frontend; actualizar caché de hooks y procesos
según el modo de ejecución en una ventana autorizada.

Después repetir el script de recepción con JWT de corta duración y test=true,
sin cookies de administrador ni callbacks: primer envío 202, repetición 200 con
igual remoteOrderId; worker debe terminar en Test sin Table Order/Fulfillment.
Confirmar que JWT incorrecto/expirado y configuración deshabilitada se rechazan,
y deshabilitar el registro de simulación al terminar. No compartir JWT ni secretos.

Rollback: revertir el commit local de esta corrección en la rama correspondiente
y refrescar caché/procesos solo con autorización. No hay cambios de datos, esquema,
precios o permisos que revertir. Mantener el cambio OpenSpec para trazabilidad.
