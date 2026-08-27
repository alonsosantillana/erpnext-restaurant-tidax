from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from erpnext.stock.get_item_details import get_pos_profile
import requests
from restaurant_management.restaurant_management.company_settings import (
    get_user_restaurant_company,
    get_restaurant_settings,
)

SUCCESS = 200
NOT_FOUND = 400
PARTY_LOOKUP_PROVIDER = (
    "ovenube_peru.nubefact_integration.doctype.api_consultas.party_lookup."
    "lookup_party_identity"
)
DOCUMENT_METHODS = {
    "Restaurant Object": {
        "_delete",
        "add_object",
        "add_order",
        "commands_food",
        "get_objects",
        "orders_list",
        "production_center_dashboard",
        "set_commands_status",
        "set_status_command",
        "set_style",
    },
    "Restaurant Fulfillment": {
        "transition_status",
    },
    "Table Order": {
        "_delete",
        "delete_item",
        "divide",
        "divide_template",
        "get_items",
        "increment_item",
        "make_invoice",
        "push_item",
        "send",
        "transfer",
        "update_item_details",
        "update_item_quantity",
    },
}

READ_ONLY_DOCUMENT_METHODS = {
    ("Restaurant Object", "commands_food"),
    ("Restaurant Object", "get_objects"),
    ("Restaurant Object", "orders_list"),
    ("Restaurant Object", "production_center_dashboard"),
    ("Table Order", "divide_template"),
    ("Table Order", "get_items"),
}

DELETE_DOCUMENT_METHODS = {
    ("Restaurant Object", "_delete"),
    ("Table Order", "_delete"),
}

# Some actions are routed through Restaurant Object for UI convenience but do
# not modify the room/table/production-center layout itself. Requiring write
# permission on Restaurant Object would also grant configuration access.
RELATED_DOCUMENT_PERMISSIONS = {
    ("Restaurant Object", "add_order"): ("Table Order", "create"),
    ("Restaurant Object", "set_commands_status"): ("Table Order", "write"),
    ("Restaurant Object", "set_status_command"): ("Table Order", "write"),
}


def _require_authenticated_user():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)


def _get_account_print_configuration(order):
    installed_apps = set(frappe.get_installed_apps())
    if "silent_print" not in installed_apps:
        frappe.throw(_("Silent Print is not installed"))

    settings = get_restaurant_settings(order=order)
    print_format = settings.print_format
    if not print_format:
        frappe.throw(_("Configure the pre-account Print Format in Restaurant Settings"))

    print_format_data = frappe.db.get_value(
        "Print Format",
        print_format,
        ["doc_type", "disabled"],
        as_dict=True,
    )
    if not print_format_data or print_format_data.doc_type != "Table Order":
        frappe.throw(_("The pre-account Print Format must belong to Table Order"))
    if print_format_data.disabled:
        frappe.throw(_("The pre-account Print Format is disabled"))

    silent_format = frappe.db.get_value(
        "Silent Print Format",
        print_format,
        [
            "default_print_type",
            "page_size",
            "custom_width",
            "custom_height",
        ],
        as_dict=True,
    )
    if not silent_format:
        frappe.throw(
            _("Create a Silent Print Format for {0}").format(print_format)
        )
    if not silent_format.default_print_type:
        frappe.throw(
            _("Configure the Print Type in Silent Print Format {0}").format(
                print_format
            )
        )
    if silent_format.page_size == "Custom" and (
        not silent_format.custom_width or not silent_format.custom_height
    ):
        frappe.throw(
            _("Configure the custom paper width and height for {0}").format(
                print_format
            )
        )

    print_user = frappe.db.get_single_value("Silent Print Settings", "print_user")
    if not print_user:
        frappe.throw(_("Configure the Print User in Silent Print Settings"))
    if not frappe.db.get_value("User", print_user, "enabled"):
        frappe.throw(_("The configured Print User is disabled"))

    tab_id = frappe.db.get_single_value("Silent Print Settings", "tab_id")
    if not tab_id:
        frappe.throw(_("Select the master printer tab before printing"))

    return frappe._dict(
        print_format=print_format,
        print_type=silent_format.default_print_type,
        print_user=print_user,
        tab_id=tab_id,
    )


@frappe.whitelist(methods=["POST"])
def print_order_account(order_name):
    """Validate, render and enqueue one restaurant pre-account print."""
    _require_authenticated_user()

    order = frappe.get_doc("Table Order", order_name)
    order.check_permission("print")
    if order.items_count == 0:
        frappe.throw(_("The order has no dishes to print"))

    configuration = _get_account_print_configuration(order)
    print_silently = frappe.get_attr(
        "silent_print.utils.print_format.print_silently"
    )
    print_silently(
        doctype="Table Order",
        name=order.name,
        print_format=configuration.print_format,
        print_type=configuration.print_type,
    )

    return {
        "queued": True,
        "print_format": configuration.print_format,
        "print_type": configuration.print_type,
    }


@frappe.whitelist()
def call(model, name, method, args=None):
    """Call an explicitly supported restaurant document action."""
    _require_authenticated_user()

    if method not in DOCUMENT_METHODS.get(model, set()):
        frappe.throw(_("Unsupported restaurant operation"), frappe.PermissionError)

    doc = frappe.get_doc(model, name)
    operation = (model, method)
    related_permission = RELATED_DOCUMENT_PERMISSIONS.get(operation)
    if operation in READ_ONLY_DOCUMENT_METHODS or related_permission:
        permission_type = "read"
    elif operation in DELETE_DOCUMENT_METHODS:
        permission_type = "delete"
    else:
        permission_type = "write"
    doc.check_permission(permission_type)

    if related_permission:
        related_doctype, related_permission_type = related_permission
        if not frappe.has_permission(related_doctype, related_permission_type):
            frappe.throw(
                _("Not permitted to {0} {1}").format(
                    related_permission_type, related_doctype
                ),
                frappe.PermissionError,
            )

    parsed_args = frappe.parse_json(args) if args else {}
    if not isinstance(parsed_args, dict):
        frappe.throw(_("Operation arguments must be an object"))

    if model == "Table Order" and permission_type == "write":
        frappe.db.sql(
            "SELECT name FROM `tabTable Order` WHERE name = %s FOR UPDATE",
            (doc.name,),
        )
        doc.reload()

    action = getattr(doc, method)
    if callable(action):
        return action(**parsed_args)

    if parsed_args:
        frappe.throw(_("This restaurant operation does not accept arguments"))

    return action


@frappe.whitelist()
def validate_link(value=None, options=None, fetch=None):
    """Validate a Link value and return only permitted fields."""
    _require_authenticated_user()

    if not options or options in {"null", "undefined"}:
        return "Ok"

    if not frappe.has_permission(options, "read"):
        frappe.throw(_("Not permitted to read {0}").format(options), frappe.PermissionError)

    meta = frappe.get_meta(options)
    fetch_fields = [field.strip() for field in (fetch or "").split(",") if field.strip()]
    invalid_fields = [field for field in fetch_fields if field != "name" and not meta.has_field(field)]
    if invalid_fields:
        frappe.throw(_("Invalid fetch fields: {0}").format(", ".join(invalid_fields)))

    permitted = frappe.get_list(options, filters={"name": value}, fields=["name"], limit_page_length=1)
    if not permitted:
        return None

    if fetch_fields:
        fetch_values = frappe.db.get_value(options, value, fetch_fields)
        if len(fetch_fields) == 1 and not isinstance(fetch_values, (list, tuple)):
            fetch_values = [fetch_values]
        else:
            fetch_values = list(fetch_values or [])
        frappe.response["fetch_values"] = fetch_values

    frappe.response["valid_value"] = value
    return "Ok"


def _clean_customer_tax_id(tax_id):
    tax_id = str(tax_id or "").strip()
    if not tax_id.isdigit() or len(tax_id) not in {8, 11}:
        frappe.throw(_("DNI must contain 8 digits and RUC must contain 11 digits"))
    return tax_id


def _find_customer_by_tax_id(tax_id):
    rows = frappe.get_list(
        "Customer",
        filters={"tax_id": tax_id},
        fields=["name", "customer_name", "tax_id", "disabled"],
        limit_page_length=1,
    )
    return dict(rows[0]) if rows else None


def _lookup_party_identity(tax_id):
    cache_key = f"restaurant_customer_lookup:{frappe.session.user}:{tax_id}"
    identity = frappe.cache.get_value(cache_key)
    if identity is None:
        try:
            identity = frappe.get_attr(PARTY_LOOKUP_PROVIDER)(tax_id)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Restaurant customer lookup error")
            frappe.throw(_("The DNI/RUC lookup service is unavailable. Please try again."))

    if not isinstance(identity, dict):
        frappe.throw(_("The DNI/RUC lookup service returned an invalid response"))
    if not identity.get("found"):
        frappe.cache.set_value(cache_key, identity, expires_in_sec=300)
        return identity
    if str(identity.get("tax_id") or "") != tax_id:
        frappe.throw(_("The DNI/RUC lookup service returned a different document"))

    expected_kind = "DNI" if len(tax_id) == 8 else "RUC"
    expected_party_type = "Individual" if len(tax_id) == 8 else "Company"
    party_name = " ".join(str(identity.get("party_name") or "").split())
    if identity.get("document_kind") != expected_kind or not party_name:
        frappe.throw(_("The DNI/RUC lookup service returned incomplete identity data"))

    identity = dict(identity)
    identity["party_name"] = party_name
    identity["party_type"] = expected_party_type
    frappe.cache.set_value(cache_key, identity, expires_in_sec=300)
    return identity


def _customer_preview(customer):
    return {
        "name": customer["name"],
        "customer_name": customer["customer_name"],
        "tax_id": customer["tax_id"],
        "disabled": bool(customer.get("disabled")),
    }


@frappe.whitelist()
def lookup_customer_identity(tax_id):
    """Find an existing customer or return a side-effect-free DNI/RUC preview."""
    _require_authenticated_user()
    if not frappe.has_permission("Customer", "read"):
        frappe.throw(_("Not permitted to read customers"), frappe.PermissionError)

    tax_id = _clean_customer_tax_id(tax_id)
    customer = _find_customer_by_tax_id(tax_id)
    if customer:
        return {
            "status": "disabled" if customer.get("disabled") else "existing",
            "customer": _customer_preview(customer),
        }

    identity = _lookup_party_identity(tax_id)
    return {
        "status": "available" if identity.get("found") else "not_found",
        "identity": identity,
        "can_create": bool(frappe.has_permission("Customer", "create")),
    }


def _is_leaf_customer_group(customer_group):
    return bool(
        customer_group
        and frappe.db.get_value("Customer Group", customer_group, "is_group") == 0
    )


def _resolve_customer_group(customer_type, pos_profile=None):
    default_group = frappe.db.get_default("Customer Group")
    if _is_leaf_customer_group(default_group):
        return default_group

    if pos_profile:
        pos_groups = frappe.get_all(
            "POS Customer Group",
            filters={"parent": pos_profile},
            pluck="customer_group",
            order_by="idx asc",
        )
        for customer_group in pos_groups:
            if _is_leaf_customer_group(customer_group):
                return customer_group

    used_groups = frappe.get_all(
        "Customer",
        filters={"disabled": 0, "customer_type": customer_type},
        fields=["customer_group", "count(name) as customer_count"],
        group_by="customer_group",
        order_by="customer_count desc",
    )
    for row in used_groups:
        if _is_leaf_customer_group(row.customer_group):
            return row.customer_group

    fallback_group = frappe.db.get_value(
        "Customer Group",
        {"is_group": 0},
        "name",
        order_by="lft asc",
    )
    if fallback_group:
        return fallback_group

    frappe.throw(_("Configure at least one non-group Customer Group before creating customers"))


def _create_customer_from_identity(identity, pos_profile=None):
    if not frappe.has_permission("Customer", "create"):
        frappe.throw(_("Not permitted to create customers"), frappe.PermissionError)

    registered_address = identity.get("registered_address") or {}
    if registered_address and not frappe.has_permission("Address", "create"):
        frappe.throw(_("Not permitted to create the customer's registered address"), frappe.PermissionError)

    customer = frappe.new_doc("Customer")
    customer.customer_name = identity["party_name"]
    customer.customer_type = identity["party_type"]
    customer.tax_id = identity["tax_id"]
    customer.customer_group = _resolve_customer_group(identity["party_type"], pos_profile)
    customer.territory = frappe.db.get_default("Territory")

    customer_meta = frappe.get_meta("Customer")
    if customer_meta.has_field("tipo_documento_identidad"):
        customer.tipo_documento_identidad = identity.get("document_type_label")
    if customer_meta.has_field("codigo_tipo_documento"):
        customer.codigo_tipo_documento = identity.get("document_type_code")
    customer.insert()

    address_name = None
    if registered_address:
        address = frappe.new_doc("Address")
        address.address_title = identity["party_name"]
        address.address_type = "Billing"
        address.address_line1 = registered_address["address_line1"]
        address.country = registered_address.get("country") or "Peru"
        address.is_primary_address = 1
        address.append("links", {
            "link_doctype": "Customer",
            "link_name": customer.name,
        })

        address_meta = frappe.get_meta("Address")
        for source, target in {
            "department": "departamento",
            "province": "provincia",
            "district": "distrito",
            "location_code": "ubigeo",
        }.items():
            if registered_address.get(source) and address_meta.has_field(target):
                address.set(target, registered_address[source])
        address.insert()
        address_name = address.name

    return customer, address_name


def _assign_customer_to_order(order, customer, client=None):
    order.customer = customer.name
    order.save()
    order.reload()
    order.synchronize({"action": "Update", "client": client})
    return order.data()


@frappe.whitelist(methods=["POST"])
def create_and_assign_customer(order_name, tax_id, client=None):
    """Create a verified customer when needed and assign it to the current order."""
    _require_authenticated_user()
    tax_id = _clean_customer_tax_id(tax_id)

    order = frappe.get_doc("Table Order", order_name)
    order.check_permission("write")

    customer_data = _find_customer_by_tax_id(tax_id)
    created = False
    address_name = None
    if customer_data:
        if customer_data.get("disabled"):
            frappe.throw(_("The customer registered with this document is disabled"))
        customer = frappe.get_doc("Customer", customer_data["name"])
        customer.check_permission("read")
    else:
        if frappe.db.exists("Customer", {"tax_id": tax_id}):
            frappe.throw(_("A customer with this document already exists"))
        identity = _lookup_party_identity(tax_id)
        if not identity.get("found"):
            frappe.throw(_("No information was found for this DNI/RUC"))
        customer, address_name = _create_customer_from_identity(identity, order.pos_profile)
        created = True

    order_data = _assign_customer_to_order(order, customer, client)
    return {
        "created": created,
        "customer": {
            "name": customer.name,
            "customer_name": customer.customer_name,
            "tax_id": customer.tax_id,
        },
        "address": address_name,
        "order": order_data,
    }



@frappe.whitelist(methods=["POST"])
def create_customer_from_identity(tax_id):
    """Create or reuse a verified DNI/RUC customer before starting an order."""
    _require_authenticated_user()
    tax_id = _clean_customer_tax_id(tax_id)

    customer_data = _find_customer_by_tax_id(tax_id)
    if customer_data:
        if customer_data.get("disabled"):
            frappe.throw(_("The customer registered with this document is disabled"))
        customer = frappe.get_doc("Customer", customer_data["name"])
        customer.check_permission("read")
        return {
            "created": False,
            "customer": _customer_preview(customer_data),
            "address": None,
        }

    if frappe.db.exists("Customer", {"tax_id": tax_id}):
        frappe.throw(_("A customer with this document already exists"))
    identity = _lookup_party_identity(tax_id)
    if not identity.get("found"):
        frappe.throw(_("No information was found for this DNI/RUC"))

    _company, pos_profile = _active_restaurant_pos_context()
    customer, address_name = _create_customer_from_identity(identity, pos_profile.name)
    return {
        "created": True,
        "customer": {
            "name": customer.name,
            "customer_name": customer.customer_name,
            "tax_id": customer.tax_id,
            "disabled": False,
        },
        "address": address_name,
    }

def _active_restaurant_pos_context():
    company = get_user_restaurant_company()
    if not company:
        frappe.throw(_("Set a default Company before creating restaurant orders"))
    if not frappe.has_permission("Company", "read", company):
        frappe.throw(_("Not permitted to use Company {0}").format(company), frappe.PermissionError)

    pos_profile = get_pos_profile(company, user=frappe.session.user)
    if not pos_profile or pos_profile.get("disabled"):
        frappe.throw(_("No enabled POS Profile is available for {0}").format(company))
    return company, pos_profile


def _existing_fulfillment_request(request_id):
    if not request_id:
        return None
    name = frappe.db.get_value(
        "Restaurant Fulfillment", {"request_id": request_id}, "name"
    )
    if not name:
        return None
    fulfillment = frappe.get_doc("Restaurant Fulfillment", name)
    fulfillment.check_permission("read")
    return {
        "created": False,
        "order": frappe.get_doc("Table Order", fulfillment.order).data(),
        "fulfillment": fulfillment.board_summary(),
    }


@frappe.whitelist(methods=["POST"])
def create_fulfillment_order(
    fulfillment_type,
    customer,
    contact_phone,
    address=None,
    delivery_reference=None,
    instructions=None,
    order_channel="Phone",
    external_order_id=None,
    promised_at=None,
    delivery_fee=0,
    payment_timing="Prepaid",
    expected_payment_method=None,
    request_id=None,
):
    """Create one delivery or pickup order without a synthetic table."""
    _require_authenticated_user()
    fulfillment_type = str(fulfillment_type or "").strip()
    if fulfillment_type not in {"Delivery", "Pickup"}:
        frappe.throw(_("Select Delivery or Pickup"))

    company, pos_profile = _active_restaurant_pos_context()
    settings = get_restaurant_settings(company=company, pos_profile=pos_profile.name)
    settings_field = "enable_delivery" if fulfillment_type == "Delivery" else "enable_pickup"
    if not cint(settings.get(settings_field)):
        frappe.throw(_("{0} is disabled for company {1}").format(fulfillment_type, company))

    request_id = str(request_id or "").strip() or None
    existing = _existing_fulfillment_request(request_id)
    if existing:
        return existing

    if not frappe.has_permission("Table Order", "create"):
        frappe.throw(_("Not permitted to create restaurant orders"), frappe.PermissionError)
    if not frappe.has_permission("Restaurant Fulfillment", "create"):
        frappe.throw(_("Not permitted to create delivery or pickup orders"), frappe.PermissionError)

    customer_doc = frappe.get_doc("Customer", customer)
    customer_doc.check_permission("read")
    if customer_doc.disabled:
        frappe.throw(_("The selected customer is disabled"))
    if address:
        address_doc = frappe.get_doc("Address", address)
        address_doc.check_permission("read")

    from restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment import address_belongs_to_customer

    if fulfillment_type == "Delivery" and not address_belongs_to_customer(address, customer):
        frappe.throw(_("The delivery address must belong to the selected customer"))
    if fulfillment_type == "Pickup" and address:
        frappe.throw(_("Pickup orders do not use a delivery address"))

    delivery_fee = flt(delivery_fee)
    if delivery_fee < 0:
        frappe.throw(_("Delivery fee cannot be negative"))
    if fulfillment_type == "Pickup" and delivery_fee:
        frappe.throw(_("Pickup orders cannot have a delivery fee"))
    delivery_fee_item = None
    if delivery_fee:
        delivery_fee_item = settings.delivery_fee_item
        if not delivery_fee_item:
            frappe.throw(_("Configure the delivery fee Item in Restaurant Settings"))

    savepoint = "restaurant_fulfillment_create"
    frappe.db.savepoint(savepoint)
    try:
        order = frappe.new_doc("Table Order")
        order.service_type = fulfillment_type
        order.status = "Attending"
        order.company = company
        order.pos_profile = pos_profile.name
        order.customer = customer_doc.name
        order.guest_count = 0
        order.taxes_and_charges = frappe.db.get_value(
            "POS Profile", pos_profile.name, "taxes_and_charges"
        )
        order.selling_price_list = pos_profile.selling_price_list
        order.insert()
        if delivery_fee:
            order.add_delivery_fee_item(delivery_fee_item, delivery_fee)
            order.reload()

        fulfillment = frappe.new_doc("Restaurant Fulfillment")
        fulfillment.order = order.name
        fulfillment.fulfillment_type = fulfillment_type
        fulfillment.customer = customer_doc.name
        fulfillment.contact_phone = contact_phone
        fulfillment.address = address
        fulfillment.delivery_reference = delivery_reference
        fulfillment.instructions = instructions
        fulfillment.order_channel = order_channel
        fulfillment.external_order_id = external_order_id
        fulfillment.promised_at = promised_at
        fulfillment.delivery_fee = delivery_fee
        fulfillment.payment_timing = payment_timing
        fulfillment.expected_payment_method = expected_payment_method
        fulfillment.request_id = request_id
        fulfillment.insert()
    except frappe.DuplicateEntryError:
        frappe.db.rollback(save_point=savepoint)
        existing = _existing_fulfillment_request(request_id)
        if existing:
            return existing
        raise

    return {
        "created": True,
        "order": order.data(),
        "fulfillment": fulfillment.board_summary(),
    }


@frappe.whitelist()
def get_fulfillment_board(fulfillment_type, include_closed=0):
    _require_authenticated_user()
    fulfillment_type = str(fulfillment_type or "").strip()
    if fulfillment_type not in {"Delivery", "Pickup"}:
        frappe.throw(_("Select Delivery or Pickup"))
    if not frappe.has_permission("Restaurant Fulfillment", "read"):
        frappe.throw(_("Not permitted to view fulfillment orders"), frappe.PermissionError)

    company, pos_profile = _active_restaurant_pos_context()
    filters = {
        "company": company,
        "pos_profile": pos_profile.name,
        "fulfillment_type": fulfillment_type,
    }
    or_filters = None
    if not cint(include_closed):
        filters["status"] = ("!=", "Cancelled")
        terminal_status = "Picked Up" if fulfillment_type == "Pickup" else "Delivered"
        or_filters = [
            ["status", "!=", terminal_status],
            ["payment_status", "!=", "Paid"],
        ]

    rows = frappe.get_list(
        "Restaurant Fulfillment",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name",
            "order",
            "fulfillment_type",
            "status",
            "customer_name_snapshot",
            "order_channel",
            "promised_at",
            "delivery_fee",
            "courier_name",
            "payment_timing",
            "payment_status",
            "creation",
            "modified",
        ],
        order_by="modified desc",
        limit_page_length=200,
    )
    if not cint(include_closed):
        terminal_status = "Picked Up" if fulfillment_type == "Pickup" else "Delivered"
        rows = [
            row
            for row in rows
            if row.status != terminal_status or row.payment_status != "Paid"
        ]

    order_names = [row.order for row in rows]
    orders = {
        row.name: row
        for row in frappe.get_all(
            "Table Order",
            filters={"name": ("in", order_names)},
            fields=["name", "amount", "status"],
            limit_page_length=len(order_names),
        )
    } if order_names else {}

    return [
        {
            **dict(row),
            "customer_name": row.customer_name_snapshot,
            "amount": flt(orders.get(row.order, {}).get("amount")),
            "order_status": orders.get(row.order, {}).get("status"),
        }
        for row in rows
    ]


@frappe.whitelist()
def get_fulfillment_counts():
    _require_authenticated_user()
    if not frappe.has_permission("Restaurant Fulfillment", "read"):
        frappe.throw(_("Not permitted to view fulfillment orders"), frappe.PermissionError)

    company, pos_profile = _active_restaurant_pos_context()
    counts = {}
    for fulfillment_type, terminal_status in {
        "Delivery": "Delivered",
        "Pickup": "Picked Up",
    }.items():
        rows = frappe.get_all(
            "Restaurant Fulfillment",
            filters={
                "company": company,
                "pos_profile": pos_profile.name,
                "fulfillment_type": fulfillment_type,
                "status": ("!=", "Cancelled"),
            },
            or_filters=[
                ["status", "!=", terminal_status],
                ["payment_status", "!=", "Paid"],
            ],
            fields=["count(name) as total"],
        )
        counts[fulfillment_type] = cint(rows[0].total) if rows else 0
    return counts


@frappe.whitelist()
def get_fulfillment_detail(name):
    _require_authenticated_user()
    fulfillment = frappe.get_doc("Restaurant Fulfillment", name)
    fulfillment.check_permission("read")
    company, pos_profile = _active_restaurant_pos_context()
    if fulfillment.company != company or fulfillment.pos_profile != pos_profile.name:
        frappe.throw(_("Fulfillment is outside the active Company or POS Profile"), frappe.PermissionError)

    order = frappe.get_doc("Table Order", fulfillment.order)
    order.check_permission("read")
    return {
        "fulfillment": fulfillment.as_dict(),
        "order": order.data(),
    }


@frappe.whitelist()
def get_posinv_summary(from_date, to_date):
    # Convierte las fechas de cadena a objetos date
    desde_fecha = getdate(from_date)
    hasta_fecha = getdate(to_date)

    # Lógica para obtener documentos en el rango de fechas
    documentos = frappe.get_all(
        "POS Invoice",
        filters={
            "posting_date": ["between", [desde_fecha, hasta_fecha]]
        },
        fields=["posting_date", "name", "docstatus", "status", "customer", "customer_name", 
                "tax_id", "address_display", "currency", "net_total", "total_taxes_and_charges", "grand_total", "total", "total_amount_discount_lines",
                "additional_discount_percentage", "discount_amount", "codigo_comprobante", "tipo_comprobante", "comprobante_electronico_manual",
                "codigo_Qr_sunat", "codigo_hash_sunat", "enlace_pdf"]
    )

    response = get_response(documentos)
    return response

@frappe.whitelist()
def get_posinv_paid(from_date, to_date):
    # Convierte las fechas de cadena a objetos date
    desde_fecha = getdate(from_date)
    hasta_fecha = getdate(to_date)

    pagos = frappe.db.sql(f"""SELECT sip.parent, sip.docstatus, sip.mode_of_payment, sip.amount FROM `tabPOS Invoice` as pi INNER JOIN
                                `tabSales Invoice Payment` as sip on pi.name = sip.parent
                                WHERE pi.posting_date BETWEEN %s AND %s
                                ORDER BY sip.parent, sip.idx asc""", (desde_fecha, hasta_fecha), as_dict=True)
                                
    response = get_response(pagos)
    return response

@frappe.whitelist()
def get_posinv_items(from_date, to_date):
    # Convierte las fechas de cadena a objetos date
    desde_fecha = getdate(from_date)
    hasta_fecha = getdate(to_date)

    productos = frappe.db.sql(f"""SELECT pii.parent, pii.docstatus, pii.item_code, pii.item_name, pii.item_group, 
                                    pii.qty, pii.stock_uom, pii.price_list_rate, pii.base_rate, pii.amount, pii.base_net_rate, pii.base_net_amount, 
                                    pii.discount_percentage, pii.discount_amount FROM `tabPOS Invoice` as pi INNER JOIN
                                    `tabPOS Invoice Item` as pii on pi.name = pii.parent
                                    WHERE pi.posting_date BETWEEN %s AND %s
                                    ORDER BY pii.parent, pii.idx asc""", (desde_fecha, hasta_fecha), as_dict=True)
                                    
    response = get_response(productos)
    return response

@frappe.whitelist()
def get_response(busqueda=None):
    if(busqueda):
        # status_code = SUCCESS
        body = busqueda
    else:
        # status_code = NOT_FOUND
        body = "No existe lo buscado"
    
    response = dict(
        # status_code = status_code,
        body = body
    )
    return response
