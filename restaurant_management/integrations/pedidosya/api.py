import frappe

from restaurant_management.integrations.pedidosya.auth import authenticate_inbound
from restaurant_management.integrations.pedidosya.parsing import PayloadError
from restaurant_management.integrations.pedidosya.service import receive_order, receive_status


def _settings(remote_id):
    name = frappe.db.get_value("PedidosYa Integration Settings", {"remote_id": remote_id, "enabled": 1}, "name")
    if not name:
        frappe.throw("PedidosYa restaurant is not enabled", frappe.DoesNotExistError)
    return frappe.get_doc("PedidosYa Integration Settings", name)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def dispatch_order(remote_id):
    settings = _settings(remote_id)
    authenticate_inbound(settings, frappe.get_request_header("Authorization"))
    try:
        result, created = receive_order(settings, frappe.request.get_json(silent=True) or {})
    except PayloadError as exc:
        frappe.local.response["http_status_code"] = 400
        frappe.local.response["reason"] = "INVALID_REQUEST"
        frappe.local.response["message"] = str(exc)
        return None
    frappe.local.response["http_status_code"] = 202 if created else 200
    frappe.local.response["remoteResponse"] = {"remoteOrderId": result["remoteOrderId"]}
    return None


@frappe.whitelist(allow_guest=True, methods=["PUT", "POST"])
def update_order_status(remote_id, remote_order_id):
    settings = _settings(remote_id)
    authenticate_inbound(settings, frappe.get_request_header("Authorization"))
    try:
        receive_status(settings, remote_order_id, frappe.request.get_json(silent=True) or {})
        frappe.local.response["http_status_code"] = 200
        return None
    except PayloadError as exc:
        frappe.local.response["http_status_code"] = 400
        frappe.local.response["reason"] = "INVALID_REQUEST"
        frappe.local.response["message"] = str(exc)
        return None
