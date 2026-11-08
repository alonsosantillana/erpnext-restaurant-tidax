"""Optional internal callbacks after Restaurant's native authentication hook."""

import frappe


def authenticate_request():
    """Invoke configured finalizers; callbacks must raise to deny a request."""
    callbacks = frappe.get_hooks("tix_mcp_read_auth_finalizers", default=[])
    if not isinstance(callbacks, (list, tuple)):
        frappe.throw("Invalid authentication finalizer configuration", frappe.PermissionError)

    # Snapshot and validate the entire list before any callback can run.
    callbacks = tuple(callbacks)
    seen = set()
    for callback in callbacks:
        if (
            not isinstance(callback, str)
            or "." not in callback
            or not all(part.isidentifier() for part in callback.split("."))
            or callback in seen
        ):
            frappe.throw("Invalid authentication finalizer configuration", frappe.PermissionError)
        seen.add(callback)

    for callback in callbacks:
        frappe.get_attr(callback)()
