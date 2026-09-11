from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

import frappe
from erpnext.stock.get_item_details import get_pos_profile
from frappe import _
from frappe.utils import (
    add_days,
    cint,
    flt,
    get_datetime,
    get_datetime_in_timezone,
    get_system_timezone,
    now_datetime,
)
from pytz import timezone

from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_settings,
    get_user_restaurant_company,
)
from restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage import (
    get_items as get_restaurant_items,
)
from restaurant_management.restaurant_management.restaurant_manage import check_exceptions


API_VERSION = "1.0"
IDEMPOTENCY_DAYS = 7
MAX_CATALOG_PAGE_LENGTH = 50
MAX_NOTES_LENGTH = 500
MAX_ORDER_QUANTITY = 100
MOBILE_REQUEST_DOCTYPE = "Restaurant Mobile Request"
ORDER_STATUS_OPEN = "Attending"
ITEM_STATUS_UNSENT = "Attending"

CATALOG_FIELDS = (
    "item_code",
    "item_name",
    "item_group",
    "image",
    "stock_uom",
    "uom",
    "price_list_rate",
    "rate",
    "actual_qty",
    "item_tax_template",
    "item_tax_rate",
    "has_batch_no",
    "has_serial_no",
)
ORDER_ITEM_FIELDS = (
    "identifier",
    "item_code",
    "item_name",
    "item_group",
    "qty",
    "rate",
    "price_list_rate",
    "amount",
    "tax_amount",
    "status",
    "notes",
    "ordered_time",
    "ordered_nro",
    "processing_started_at",
    "completed_at",
    "preparation_time_target",
    "waiting_time_minutes",
    "preparation_time_minutes",
    "total_time_minutes",
)


def _set_http_status(status_code: int) -> None:
    try:
        frappe.local.response["http_status_code"] = status_code
    except (AttributeError, TypeError):
        pass


def _fail(code: str, message: str, status_code: int = 400, exc=None):
    _set_http_status(status_code)
    exception = exc or frappe.ValidationError
    frappe.throw(f"{code}: {_(message)}", exception)


def _require_authenticated_user() -> str:
    user = getattr(frappe.session, "user", None)
    if not user or user == "Guest":
        _fail(
            "AUTHENTICATION_REQUIRED",
            "Authentication required",
            401,
            frappe.AuthenticationError,
        )
    if not frappe.db.get_value("User", user, "enabled"):
        _fail("USER_DISABLED", "The authenticated user is disabled", 401, frappe.AuthenticationError)
    return user


def _profile_value(profile, fieldname: str):
    if hasattr(profile, "get"):
        return profile.get(fieldname)
    return getattr(profile, fieldname, None)


def _active_context(company: str | None = None, pos_profile: str | None = None):
    user = _require_authenticated_user()
    active_company = get_user_restaurant_company()
    if not active_company:
        _fail("COMPANY_REQUIRED", "Set a default Company before using Resto Tix")
    if company and company != active_company:
        _fail(
            "COMPANY_NOT_ALLOWED",
            "The requested Company is not active for this user",
            403,
            frappe.PermissionError,
        )
    if not frappe.has_permission("Company", "read", active_company):
        _fail(
            "COMPANY_NOT_ALLOWED",
            "Not permitted to use the active Company",
            403,
            frappe.PermissionError,
        )

    profile = get_pos_profile(active_company, user=user)
    profile_name = _profile_value(profile, "name") if profile else None
    if not profile_name or cint(_profile_value(profile, "disabled")):
        _fail("POS_PROFILE_REQUIRED", "No enabled POS Profile is assigned to this user")
    if pos_profile and pos_profile != profile_name:
        _fail(
            "POS_PROFILE_NOT_ALLOWED",
            "The requested POS Profile is not assigned to this user",
            403,
            frappe.PermissionError,
        )

    profile_company = _profile_value(profile, "company") or frappe.db.get_value(
        "POS Profile", profile_name, "company"
    )
    if profile_company != active_company:
        _fail("POS_PROFILE_COMPANY_MISMATCH", "POS Profile belongs to another Company")

    return frappe._dict(
        user=user,
        company=active_company,
        pos_profile=profile_name,
        profile=profile,
        settings=get_restaurant_settings(company=active_company),
    )


def _allowed_rooms(context) -> list[str]:
    permissions = frappe.permissions.get_doc_permissions(
        frappe.new_doc("Restaurant Object")
    )
    if context.user == "Administrator" or permissions.get("write") or permissions.get("create"):
        room_names = frappe.get_all(
            "Restaurant Object",
            filters={"type": "Room", "company": context.company},
            pluck="name",
        )
    else:
        room_names = list(context.settings.rooms_access())

    if not room_names:
        return []
    return frappe.get_all(
        "Restaurant Object",
        filters={
            "name": ("in", room_names),
            "type": "Room",
            "company": context.company,
        },
        pluck="name",
        order_by="description asc, name asc",
    )


def _restaurant_access_allowed(kind: str, action: str, doc, context) -> bool:
    if context.user == "Administrator":
        return True
    if not frappe.has_permission(doc.doctype, action, doc):
        return False

    restricted = cint(context.settings.get(f"restricted_to_owner_{kind}"))
    if not restricted:
        return True
    if kind == "order" and (doc.get("cambio_mozo") or doc.owner) == context.user:
        return True

    role_profile = frappe.db.get_value("User", context.user, "role_profile_name")
    for exception in context.settings.get("restaurant_exceptions", []):
        if exception.role_profile == role_profile and cint(exception.get(f"{kind}_{action}")):
            return True
    return False


def _validate_table_access(table, context) -> None:
    if table.doctype != "Restaurant Object" or table.type != "Table":
        _fail("TABLE_NOT_FOUND", "The requested restaurant table does not exist", 404)
    if table.company != context.company or table.room not in _allowed_rooms(context):
        _fail(
            "TABLE_NOT_ALLOWED",
            "The requested table is outside the authorized restaurant scope",
            403,
            frappe.PermissionError,
        )
    try:
        check_exceptions(
            {"name": "Restaurant Object", "short_name": "table", "action": "read", "data": table},
            "The requested table is not permitted",
        )
    except frappe.ValidationError:
        _fail(
            "TABLE_NOT_ALLOWED",
            "The requested table is not permitted",
            403,
            frappe.PermissionError,
        )


def _validate_order_access(order, context, action: str = "read") -> None:
    if order.company != context.company or order.pos_profile != context.pos_profile:
        _fail(
            "ORDER_NOT_ALLOWED",
            "The requested order is outside the authorized POS context",
            403,
            frappe.PermissionError,
        )
    if order.room not in _allowed_rooms(context):
        _fail(
            "ORDER_NOT_ALLOWED",
            "The requested order belongs to an unauthorized room",
            403,
            frappe.PermissionError,
        )
    try:
        check_exceptions(
            {"name": "Table Order", "short_name": "order", "action": action, "data": order},
            "The requested order is not permitted",
        )
    except frappe.ValidationError:
        _fail(
            "ORDER_NOT_ALLOWED",
            "The requested order is not permitted",
            403,
            frappe.PermissionError,
        )
    if action == "write" and order.status != ORDER_STATUS_OPEN:
        _fail("ORDER_NOT_OPEN", "Only an active order can be changed", 409)


def _system_naive(value):
    value = get_datetime(value)
    if value.tzinfo is not None:
        value = value.astimezone(timezone(get_system_timezone())).replace(tzinfo=None)
    return value


def _rfc3339(value) -> str:
    value = _system_naive(value)
    return timezone(get_system_timezone()).localize(value).isoformat(timespec="microseconds")


def _server_time() -> str:
    return get_datetime_in_timezone(get_system_timezone()).isoformat(timespec="microseconds")


def _latest_order_modified(order):
    values = [get_datetime(order.modified)]
    children = frappe.get_all(
        "Order Entry Item",
        filters={"parenttype": "Table Order", "parent": order.name},
        fields=["modified"],
        order_by="modified desc",
        limit_page_length=1,
    )
    if children and children[0].modified:
        values.append(get_datetime(children[0].modified))
    return max(values)


def _order_version(order) -> str:
    return _rfc3339(_latest_order_modified(order))


def _assert_order_version(order, expected_order_version: str) -> None:
    if not expected_order_version:
        _fail("ORDER_VERSION_REQUIRED", "Expected order version is required")
    try:
        expected = _system_naive(expected_order_version)
    except (TypeError, ValueError, frappe.ValidationError):
        _fail("ORDER_VERSION_INVALID", "Expected order version is invalid")
    current = _latest_order_modified(order)
    if expected != current:
        _fail(
            "ORDER_VERSION_CONFLICT",
            "The order changed in another session",
            409,
        )


def _item_payload(item) -> dict[str, Any]:
    source = dict(item or {})
    return {field: source.get(field) for field in ORDER_ITEM_FIELDS}


def _order_payload(order) -> dict[str, Any]:
    return {
        "name": order.name,
        "company": order.company,
        "pos_profile": order.pos_profile,
        "room": order.room,
        "table": order.table,
        "status": order.status,
        "customer": order.customer,
        "customer_name": order.customer_name,
        "guest_count": cint(order.guest_count),
        "currency": frappe.db.get_value("POS Profile", order.pos_profile, "currency"),
        "selling_price_list": order.selling_price_list,
        "tax": flt(order.tax),
        "amount": flt(order.amount),
        "items_count": order.items_count,
        "products_not_ordered": order.products_not_ordered_count,
        "items": [_item_payload(item) for item in order.items_list()],
    }


def _envelope(data, order=None) -> dict[str, Any]:
    result = {"api_version": API_VERSION, "data": data, "server_time": _server_time()}
    if order is not None:
        result["order_version"] = _order_version(order)
    return result


def _parse_client_request_id(value: str) -> str:
    try:
        parsed = uuid.UUID(str(value or ""))
    except (ValueError, AttributeError, TypeError):
        _fail("CLIENT_REQUEST_ID_INVALID", "client_request_id must be a UUID")
    return str(parsed)


def _canonical_hash(action: str, order_name: str | None, payload: dict[str, Any]) -> str:
    body = json.dumps(
        {"action": action, "order": order_name, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _request_key(user: str, client_request_id: str) -> str:
    return hashlib.sha256(f"{user}\0{client_request_id}".encode("utf-8")).hexdigest()


def _load_existing_request(request_key: str):
    name = frappe.db.get_value(MOBILE_REQUEST_DOCTYPE, {"request_key": request_key}, "name")
    if not name:
        return None
    frappe.db.sql(
        "SELECT name FROM `tabRestaurant Mobile Request` WHERE name = %s FOR UPDATE",
        (name,),
    )
    return frappe.get_doc(MOBILE_REQUEST_DOCTYPE, name)


def _begin_request(
    action: str,
    order_name: str | None,
    client_request_id: str,
    payload: dict[str, Any],
):
    user = frappe.session.user
    client_request_id = _parse_client_request_id(client_request_id)
    request_key = _request_key(user, client_request_id)
    request_hash = _canonical_hash(action, order_name, payload)
    existing = _load_existing_request(request_key)
    if existing:
        if existing.request_hash != request_hash:
            _fail(
                "CLIENT_REQUEST_ID_REUSED",
                "client_request_id was already used with a different payload",
                409,
            )
        if existing.status == "Completed" and existing.response_json:
            return existing, json.loads(existing.response_json)
        _fail("REQUEST_IN_PROGRESS", "The request is still being processed", 409)

    request_doc = frappe.get_doc(
        {
            "doctype": MOBILE_REQUEST_DOCTYPE,
            "request_key": request_key,
            "client_request_id": client_request_id,
            "requested_by": user,
            "order": order_name,
            "action": action,
            "request_hash": request_hash,
            "status": "Processing",
            "requested_on": now_datetime(),
            "expires_on": add_days(now_datetime(), IDEMPOTENCY_DAYS),
        }
    )
    try:
        request_doc.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        existing = _load_existing_request(request_key)
        if existing and existing.request_hash == request_hash and existing.status == "Completed":
            return existing, json.loads(existing.response_json)
        _fail("REQUEST_IN_PROGRESS", "The request is still being processed", 409)
    return request_doc, None


def _complete_request(request_doc, response: dict[str, Any], order_name: str | None = None) -> None:
    request_doc.order = order_name or request_doc.order
    request_doc.status = "Completed"
    request_doc.completed_on = now_datetime()
    request_doc.response_json = frappe.as_json(response)
    request_doc.save(ignore_permissions=True)


def _lock_order(order_name: str):
    frappe.db.sql(
        "SELECT name FROM `tabTable Order` WHERE name = %s FOR UPDATE",
        (order_name,),
    )
    order = frappe.get_doc("Table Order", order_name)
    order.reload()
    return order


def _positive_integer(value, fieldname: str, maximum: int = MAX_ORDER_QUANTITY) -> int:
    numeric = flt(value)
    if numeric < 1 or numeric != cint(numeric) or numeric > maximum:
        _fail(
            "INVALID_QUANTITY",
            f"{fieldname} must be a whole number between 1 and {maximum}",
        )
    return cint(numeric)


@frappe.whitelist(methods=["GET"])
def get_context(company=None, pos_profile=None):
    context = _active_context(company, pos_profile)
    rooms = _allowed_rooms(context)
    return _envelope(
        {
            "user": {"name": context.user, "full_name": frappe.utils.get_fullname(context.user)},
            "company": context.company,
            "pos_profile": context.pos_profile,
            "rooms": rooms,
            "capabilities": {
                "can_read_orders": bool(frappe.has_permission("Table Order", "read")),
                "can_create_order": bool(frappe.has_permission("Table Order", "create")),
                "can_update_order": bool(frappe.has_permission("Table Order", "write")),
                "can_send_command": bool(frappe.has_permission("Table Order", "write")),
                "can_pay": False,
            },
        }
    )


@frappe.whitelist(methods=["GET"])
def get_tables(company=None, pos_profile=None):
    context = _active_context(company, pos_profile)
    room_names = _allowed_rooms(context)
    if not room_names:
        return _envelope({"rooms": [], "tables": []})

    rooms = frappe.get_all(
        "Restaurant Object",
        filters={"name": ("in", room_names), "type": "Room", "company": context.company},
        fields=["name", "description"],
        order_by="description asc, name asc",
    )
    tables = frappe.get_all(
        "Restaurant Object",
        filters={"room": ("in", room_names), "type": "Table", "company": context.company},
        fields=["name", "description", "room", "no_of_seats", "color", "shape", "current_user"],
        order_by="room asc, description asc, name asc",
    )
    table_names = [table.name for table in tables]
    active_by_table = {}
    if table_names:
        active_orders = frappe.get_all(
            "Table Order",
            filters={
                "table": ("in", table_names),
                "company": context.company,
                "status": ORDER_STATUS_OPEN,
            },
            fields=[
                "name", "table", "owner", "cambio_mozo", "guest_count", "amount", "tax", "modified",
            ],
            order_by="creation asc",
        )
        for row in active_orders:
            if row.table in active_by_table:
                continue
            order = frappe.get_doc("Table Order", row.name)
            if _restaurant_access_allowed("order", "read", order, context):
                active_by_table[row.table] = {
                    "name": row.name,
                    "guest_count": cint(row.guest_count),
                    "amount": flt(row.amount),
                    "tax": flt(row.tax),
                    "version": _order_version(order),
                }

    return _envelope(
        {
            "rooms": [dict(room) for room in rooms],
            "tables": [
                {
                    "name": table.name,
                    "description": table.description,
                    "room": table.room,
                    "no_of_seats": cint(table.no_of_seats),
                    "color": table.color,
                    "shape": table.shape,
                    "occupied_by_me": table.current_user == context.user,
                    "active_order": active_by_table.get(table.name),
                }
                for table in tables
            ],
        }
    )


@frappe.whitelist(methods=["GET"])
def get_catalog(
    company=None,
    pos_profile=None,
    search_value="",
    item_group=None,
    start=0,
    page_length=20,
):
    context = _active_context(company, pos_profile)
    start = max(0, cint(start))
    page_length = _positive_integer(page_length, "page_length", MAX_CATALOG_PAGE_LENGTH)
    search_value = str(search_value or "").strip()
    if len(search_value) > 120:
        _fail("SEARCH_TOO_LONG", "Catalog search is too long")

    price_list = _profile_value(context.profile, "selling_price_list") or frappe.db.get_value(
        "POS Profile", context.pos_profile, "selling_price_list"
    )
    result = get_restaurant_items(
        start=start,
        page_length=page_length,
        price_list=price_list,
        pos_profile=context.pos_profile,
        item_group=item_group,
        search_value=search_value,
    )
    raw_items = result if isinstance(result, list) else (result or {}).get("items", [])
    items = []
    for row in raw_items:
        source = dict(row)
        items.append({field: source.get(field) for field in CATALOG_FIELDS})
    return _envelope(
        {
            "items": items,
            "pagination": {
                "start": start,
                "page_length": page_length,
                "count": len(items),
                "has_more": len(items) == page_length,
            },
        }
    )


@frappe.whitelist(methods=["GET"])
def get_order(order_name, company=None, pos_profile=None):
    context = _active_context(company, pos_profile)
    order = frappe.get_doc("Table Order", order_name)
    _validate_order_access(order, context, "read")
    return _envelope(_order_payload(order), order)


@frappe.whitelist(methods=["POST"])
def open_order(table_name, guest_count, client_request_id, company=None, pos_profile=None):
    context = _active_context(company, pos_profile)
    guest_count = _positive_integer(guest_count, "guest_count", 100)
    request_payload = {"table_name": table_name, "guest_count": guest_count}
    request_doc, cached = _begin_request(
        "open_order", None, client_request_id, request_payload
    )
    if cached is not None:
        return cached

    frappe.db.sql(
        "SELECT name FROM `tabRestaurant Object` WHERE name = %s FOR UPDATE",
        (table_name,),
    )
    table = frappe.get_doc("Restaurant Object", table_name)
    table.reload()
    _validate_table_access(table, context)

    active_names = frappe.get_all(
        "Table Order",
        filters={
            "table": table.name,
            "company": context.company,
            "status": ORDER_STATUS_OPEN,
        },
        pluck="name",
        order_by="creation asc",
    )
    if len(active_names) > 1:
        _fail("MULTIPLE_ACTIVE_ORDERS", "The table has more than one active order", 409)
    if active_names:
        order = frappe.get_doc("Table Order", active_names[0])
        _validate_order_access(order, context, "read")
    else:
        if not frappe.has_permission("Table Order", "create"):
            _fail(
                "ORDER_CREATE_NOT_ALLOWED",
                "Not permitted to create restaurant orders",
                403,
                frappe.PermissionError,
            )
        table.add_order(client=client_request_id)
        active_names = frappe.get_all(
            "Table Order",
            filters={
                "table": table.name,
                "company": context.company,
                "status": ORDER_STATUS_OPEN,
            },
            pluck="name",
            order_by="creation desc",
            limit_page_length=2,
        )
        if len(active_names) != 1:
            _fail("ORDER_OPEN_FAILED", "The restaurant order could not be opened", 409)
        order = frappe.get_doc("Table Order", active_names[0])

    if cint(order.guest_count) != guest_count:
        _validate_order_access(order, context, "write")
        order.guest_count = guest_count
        order.save()
    response = _envelope(_order_payload(order), order)
    _complete_request(request_doc, response, order.name)
    return response


def _new_item_entry(context, item_code: str, quantity: int, notes: str, identifier: str):
    price_list = _profile_value(context.profile, "selling_price_list") or frappe.db.get_value(
        "POS Profile", context.pos_profile, "selling_price_list"
    )
    catalog_result = get_restaurant_items(
        start=0,
        page_length=MAX_CATALOG_PAGE_LENGTH,
        price_list=price_list,
        pos_profile=context.pos_profile,
        item_group=None,
        search_value=item_code,
    )
    catalog_rows = (
        catalog_result
        if isinstance(catalog_result, list)
        else (catalog_result or {}).get("items", [])
    )
    catalog_item = next(
        (dict(row) for row in catalog_rows if row.get("item_code") == item_code),
        None,
    )
    if not catalog_item:
        _fail(
            "ITEM_NOT_AVAILABLE",
            "The requested item is not available in this POS Profile",
            404,
        )

    item = frappe.db.get_value(
        "Item",
        item_code,
        [
            "name",
            "item_name",
            "stock_uom",
            "disabled",
            "is_sales_item",
            "has_batch_no",
            "has_serial_no",
        ],
        as_dict=True,
    )
    if not item or item.disabled or not item.is_sales_item:
        _fail("ITEM_NOT_AVAILABLE", "The requested item is not available for sale", 404)
    if item.has_batch_no or item.has_serial_no:
        _fail(
            "ITEM_TRACKING_NOT_SUPPORTED",
            "Batch- or serial-controlled items are not supported by the mobile MVP",
        )
    price_list_rate = flt(
        catalog_item.get("price_list_rate") or catalog_item.get("rate")
    )
    return {
        "identifier": identifier,
        "item_code": item.name,
        "item_name": item.item_name,
        "stock_uom": item.stock_uom,
        "qty": quantity,
        "rate": price_list_rate,
        "price_list_rate": price_list_rate,
        "discount_percentage": 0,
        "discount_amount": 0,
        "status": ITEM_STATUS_UNSENT,
        "notes": notes,
        "ordered_time": None,
        "ordered_nro": 0,
        "ordered_finish": 0,
        "processing_started_at": None,
        "processing_started_by": None,
        "completed_at": None,
        "completed_by": None,
        "waiting_time_minutes": 0,
        "preparation_time_minutes": 0,
        "total_time_minutes": 0,
        "preparation_time_target": 0,
        "preparation_time_source": None,
        "has_batch_no": 0,
        "batch_no": None,
        "has_serial_no": 0,
        "serial_no": None,
        "unit_value": 0,
        "item_tax_template": catalog_item.get("item_tax_template"),
        "item_tax_rate": catalog_item.get("item_tax_rate") or "{}",
    }


@frappe.whitelist(methods=["POST"])
def mutate_item(
    order_name,
    action,
    client_request_id,
    expected_order_version,
    item_code=None,
    identifier=None,
    quantity=None,
    notes=None,
    company=None,
    pos_profile=None,
):
    context = _active_context(company, pos_profile)
    action = str(action or "").strip()
    if action not in {"add", "set_quantity", "set_note", "remove"}:
        _fail("ITEM_ACTION_NOT_SUPPORTED", "Unsupported mobile item operation")

    clean_notes = str(notes or "")
    if len(clean_notes) > MAX_NOTES_LENGTH:
        _fail("NOTES_TOO_LONG", "Item notes exceed the maximum length")
    clean_quantity = None
    if action in {"add", "set_quantity"}:
        clean_quantity = _positive_integer(quantity, "quantity")
    if action == "add" and not item_code:
        _fail("ITEM_CODE_REQUIRED", "item_code is required")
    if action != "add" and not identifier:
        _fail("ITEM_IDENTIFIER_REQUIRED", "identifier is required")

    request_payload = {
        "action": action,
        "item_code": item_code,
        "identifier": identifier,
        "quantity": clean_quantity,
        "notes": clean_notes,
        "expected_order_version": expected_order_version,
    }
    request_doc, cached = _begin_request(
        "mutate_item", order_name, client_request_id, request_payload
    )
    if cached is not None:
        return cached

    order = _lock_order(order_name)
    _validate_order_access(order, context, "write")
    _assert_order_version(order, expected_order_version)

    if action == "add":
        stable_identifier = f"rtx-{uuid.UUID(_parse_client_request_id(client_request_id)).hex}"
        entry = _new_item_entry(
            context, item_code, clean_quantity, clean_notes, stable_identifier
        )
        order.push_item(entry)
    elif action == "set_quantity":
        order.update_item_quantity(identifier, clean_quantity, client=client_request_id)
    elif action == "set_note":
        matching = [item for item in order.entry_items if item.identifier == identifier]
        if len(matching) != 1:
            _fail("ITEM_NOT_FOUND", "The selected order item does not exist", 404)
        order.update_item_details(
            identifier,
            notes=clean_notes,
            discount_percentage=matching[0].discount_percentage,
            client=client_request_id,
        )
    else:
        matching = [item for item in order.entry_items if item.identifier == identifier]
        if len(matching) != 1:
            _fail("ITEM_NOT_FOUND", "The selected order item does not exist", 404)
        if matching[0].status != ITEM_STATUS_UNSENT:
            _fail("ITEM_ALREADY_SENT", "Only unsent items can be removed", 409)
        frappe.db.delete(
            "Order Entry Item",
            {"parenttype": "Table Order", "parent": order.name, "identifier": identifier},
        )
        order.reload()
        order.aggregate()
        order.synchronize(
            {"action": "queue", "item_removed": identifier, "status": [ITEM_STATUS_UNSENT]}
        )

    order.reload()
    response = _envelope(_order_payload(order), order)
    _complete_request(request_doc, response, order.name)
    return response


@frappe.whitelist(methods=["POST"])
def send_command(
    order_name,
    client_request_id,
    expected_order_version,
    company=None,
    pos_profile=None,
):
    context = _active_context(company, pos_profile)
    request_payload = {"expected_order_version": expected_order_version}
    request_doc, cached = _begin_request(
        "send_command", order_name, client_request_id, request_payload
    )
    if cached is not None:
        return cached

    order = _lock_order(order_name)
    _validate_order_access(order, context, "write")
    _assert_order_version(order, expected_order_version)
    if not any(item.status == ITEM_STATUS_UNSENT for item in order.entry_items):
        _fail("NO_UNSENT_ITEMS", "The order has no unsent items", 409)

    order.send
    order.reload()
    response = _envelope(_order_payload(order), order)
    _complete_request(request_doc, response, order.name)
    return response


@frappe.whitelist(methods=["GET"])
def get_changes(since, company=None, pos_profile=None, limit=100):
    context = _active_context(company, pos_profile)
    try:
        if not since:
            raise ValueError
        since_value = _system_naive(since)
    except (TypeError, ValueError, frappe.ValidationError):
        _fail("SYNC_MARKER_INVALID", "Synchronization marker is invalid")
    limit = _positive_integer(limit, "limit", 100)
    upper_bound = now_datetime()
    next_marker = _rfc3339(upper_bound)
    room_names = _allowed_rooms(context)
    if not room_names:
        return _envelope({"orders": [], "next_marker": next_marker, "truncated": False})

    active_names = frappe.get_all(
        "Table Order",
        filters={
            "room": ("in", room_names),
            "company": context.company,
            "pos_profile": context.pos_profile,
            "status": ORDER_STATUS_OPEN,
        },
        pluck="name",
        limit_page_length=0,
    )
    if not active_names:
        changed_children = []
    else:
        changed_children = frappe.get_all(
            "Order Entry Item",
            filters=[
                ["parenttype", "=", "Table Order"],
                ["parent", "in", active_names],
                ["modified", ">", since_value],
                ["modified", "<=", upper_bound],
            ],
            pluck="parent",
            limit_page_length=0,
        )

    changed_parents = frappe.get_all(
        "Table Order",
        filters=[
            ["room", "in", room_names],
            ["company", "=", context.company],
            ["pos_profile", "=", context.pos_profile],
            ["modified", ">", since_value],
            ["modified", "<=", upper_bound],
        ],
        pluck="name",
        limit_page_length=0,
    )
    candidates = set(changed_parents) | set(changed_children)
    changed = []
    for name in candidates:
        order = frappe.get_doc("Table Order", name)
        if not _restaurant_access_allowed("order", "read", order, context):
            continue
        latest_modified = _latest_order_modified(order)
        if since_value < latest_modified <= upper_bound:
            changed.append(_envelope(_order_payload(order), order))
    changed.sort(key=lambda item: item["order_version"])
    truncated = len(changed) > limit
    if truncated:
        next_marker = changed[limit - 1]["order_version"]

    return _envelope(
        {
            "orders": changed[:limit],
            "next_marker": next_marker,
            "truncated": truncated,
        }
    )
