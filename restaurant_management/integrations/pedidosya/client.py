from ipaddress import ip_address
from urllib.parse import urlparse

import frappe
import requests
from frappe import _


TIMEOUT = (5, 20)


def _allowed_hosts(settings):
    hosts = {line.strip().lower() for line in str(settings.callback_allowed_hosts or "").splitlines() if line.strip()}
    api_host = urlparse(settings.api_base_url or "").hostname
    if api_host:
        hosts.add(api_host.lower())
    return hosts


def validate_callback_url(settings, url):
    parsed = urlparse(str(url or ""))
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        frappe.throw(_("PedidosYa callback URL must use HTTPS"))
    try:
        address = ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local:
            frappe.throw(_("PedidosYa callback URL cannot target a private address"))
    except ValueError:
        pass
    if host not in _allowed_hosts(settings):
        frappe.throw(_("PedidosYa callback host is not allowed: {0}").format(host))
    return url


def _access_token(settings):
    cache_key = f"pedidosya:access-token:{settings.name}"
    cached = frappe.cache.get_value(cache_key)
    if cached:
        return cached
    response = requests.post(
        f"{str(settings.api_base_url).rstrip('/')}/v2/login",
        data={
            "grant_type": "client_credentials",
            "username": settings.api_username,
            "password": settings.get_password("api_password"),
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise ValueError("PedidosYa login did not return access_token")
    frappe.cache.set_value(cache_key, token, expires_in_sec=max(int(data.get("expires_in") or 1800) - 60, 60))
    return token


def post_callback(settings, url, payload=None):
    validate_callback_url(settings, url)
    kwargs = {
        "headers": {"Authorization": f"Bearer {_access_token(settings)}"},
        "timeout": TIMEOUT,
    }
    if payload is not None:
        kwargs["json"] = payload
    response = requests.post(url, **kwargs)
    response.raise_for_status()
    return response.json() if response.content else {}
