import jwt

import frappe
from frappe import _


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

    kwargs = {
        "algorithms": [settings.jwt_algorithm or "HS512"],
        "leeway": settings.jwt_leeway_seconds or 30,
        "options": {},
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
