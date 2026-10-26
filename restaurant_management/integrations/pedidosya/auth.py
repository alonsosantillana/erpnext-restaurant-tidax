import jwt

import frappe
from frappe import _


_INBOUND_METHODS = {
    "restaurant_management.integrations.pedidosya.api.dispatch_order": {"POST"},
    "restaurant_management.integrations.pedidosya.api.update_order_status": {"POST", "PUT"},
}
_INBOUND_ROUTES = {
    prefix + method: (method, http_methods)
    for prefix in ("/api/method/", "/api/v1/method/")
    for method, http_methods in _INBOUND_METHODS.items()
}
_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}


def get_enabled_settings(remote_id):
    """Use the same validated vendor lookup in the auth hook and endpoints."""
    if not isinstance(remote_id, str) or not remote_id.strip():
        frappe.throw(_("Invalid PedidosYa integration configuration"), frappe.AuthenticationError)
    remote_id = remote_id.strip()
    name = frappe.db.get_value(
        "PedidosYa Integration Settings", {"remote_id": remote_id, "enabled": 1}, "name"
    )
    if not name:
        frappe.throw(_("Invalid PedidosYa integration configuration"), frappe.AuthenticationError)
    settings = frappe.get_doc("PedidosYa Integration Settings", name)
    if not settings.enabled or settings.remote_id != remote_id:
        frappe.throw(_("Invalid PedidosYa integration configuration"), frappe.AuthenticationError)
    return settings


def authenticate_request():
    """Authenticate only exact middleware routes before Frappe's Guest guard."""
    request = getattr(frappe.local, "request", None)
    if request is None:
        return
    route = _INBOUND_ROUTES.get(request.path)
    if route is None:
        return
    method, http_methods = route
    if request.method not in http_methods:
        return

    form_dict = frappe.local.form_dict
    # app.application prioritizes cmd over the URL, and execute_cmd applies
    # overrides. Neither may redirect a middleware JWT to an unrelated method.
    if (form_dict.get("cmd") and form_dict.cmd != method) or (
        frappe.override_whitelisted_method(method) != method
    ):
        frappe.throw(_("Invalid PedidosYa authentication target"), frappe.AuthenticationError)

    settings = get_enabled_settings(form_dict.get("remote_id"))
    authenticate_inbound(settings, frappe.get_request_header("Authorization"))
    user = settings.integration_user
    if (
        not isinstance(user, str)
        or not user
        or user in {"Guest", "Administrator"}
        or not frappe.db.get_value("User", user, "enabled")
    ):
        frappe.throw(_("Invalid PedidosYa integration user"), frappe.AuthenticationError)

    # set_user resets form_dict. Preserve the validated request parameters, as
    # Frappe's own OAuth/API-key authentication does; do not create a login session.
    frappe.set_user(user)
    frappe.local.form_dict = form_dict


def get_bearer_token(authorization):
    scheme, separator, token = str(authorization or "").strip().partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        frappe.throw(_("Missing PedidosYa bearer token"), frappe.AuthenticationError)
    return token.strip()


def authenticate_inbound(settings, authorization):
    """Verify the middleware JWT with the secret stored in Password storage."""
    token = get_bearer_token(authorization)
    secret = settings.get_password("jwt_secret")
    if not secret:
        frappe.throw(_("PedidosYa JWT secret is not configured"), frappe.AuthenticationError)

    algorithm = settings.jwt_algorithm or "HS512"
    if algorithm not in _JWT_ALGORITHMS:
        frappe.throw(_("Invalid PedidosYa JWT algorithm"), frappe.AuthenticationError)
    kwargs = {
        "algorithms": [algorithm],
        "leeway": settings.jwt_leeway_seconds if settings.jwt_leeway_seconds is not None else 30,
        "options": {"require": ["exp", "service"]},
    }
    if settings.jwt_audience:
        kwargs["audience"] = settings.jwt_audience
    else:
        kwargs["options"]["verify_aud"] = False
    if settings.jwt_issuer:
        kwargs["issuer"] = settings.jwt_issuer

    try:
        claims = jwt.decode(token, secret, **kwargs)
        if claims.get("service") != "middleware":
            raise jwt.InvalidTokenError("unexpected service claim")
        return claims
    except jwt.PyJWTError:
        frappe.throw(_("Invalid or expired PedidosYa token"), frappe.AuthenticationError)
