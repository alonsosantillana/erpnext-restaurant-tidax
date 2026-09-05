# Diseño

La transacción de pago conserva como límite atómico la creación de la Factura POS y el enlace con Table Order. Antes de finalizar marca la emisión como `Queued` y registra un callback `enqueue_after_commit`; un rollback no deja un trabajo huérfano.

El trabajador serializa cada comprobante mediante un lock por nombre. Cambia el estado a `Sending`, incrementa el contador y confirma ese estado antes de acceder al proveedor. Siempre consulta primero: si Nubefact ya conoce el comprobante, persiste la respuesta; solo genera cuando la consulta devuelve explícitamente `not_found` o código `24`.

Una respuesta aceptada termina en `Accepted` y conserva la cola de impresión existente. Una respuesta rechazada termina en `Rejected`. Un timeout, error de transporte o resultado ambiguo termina en `Retry Required`. El scheduler recupera `Queued` y `Retry Required`, además de `Sending` abandonados, hasta tres intentos automáticos. Un reintento autorizado puede reencolar manualmente después de corregir la causa.

La interfaz deja de ejecutar el envío fiscal directamente. Muestra que la emisión está en proceso y consulta el estado durante un periodo corto sin congelar Restaurant Manage; el trabajo continúa aunque se cierre la pestaña.
