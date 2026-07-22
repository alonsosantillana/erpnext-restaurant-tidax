import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, strip_html


FULFILLMENT_TRANSITIONS = {
    "Delivery": {
        "New": {"Preparing", "Cancelled"},
        "Preparing": {"Ready", "Cancelled"},
        "Ready": {"Preparing", "Assigned", "Cancelled"},
        "Assigned": {"Preparing", "Out for Delivery", "Cancelled"},
        "Out for Delivery": {"Delivered", "Delivery Failed"},
        "Delivery Failed": {"Assigned", "Cancelled"},
        "Delivered": set(),
        "Cancelled": set(),
    },
    "Pickup": {
        "New": {"Preparing", "Cancelled"},
        "Preparing": {"Ready", "Cancelled"},
        "Ready": {"Preparing", "Picked Up", "Cancelled"},
        "Picked Up": set(),
        "Cancelled": set(),
    },
}

PREPARATION_COMPLETE_STATUSES = {"Completed", "Delivering", "Delivered", "Invoiced"}
IMMUTABLE_LOGISTICS_STATUSES = {"Out for Delivery", "Delivered", "Picked Up", "Cancelled"}
LOGISTICS_FIELDS = (
    "customer",
    "contact_phone",
    "address",
    "delivery_reference",
    "instructions",
    "delivery_fee",
)


def address_belongs_to_customer(address, customer):
    if not address or not customer:
        return False
    return bool(
        frappe.db.exists(
            "Dynamic Link",
            {
                "parenttype": "Address",
                "parent": address,
                "link_doctype": "Customer",
                "link_name": customer,
            },
        )
    )


def render_address_snapshot(address_name):
    address = frappe.get_doc("Address", address_name)
    fields = (
        "address_line1",
        "address_line2",
        "district",
        "distrito",
        "city",
        "county",
        "province",
        "provincia",
        "state",
        "department",
        "departamento",
        "pincode",
        "country",
    )
    parts = []
    for fieldname in fields:
        value = strip_html(str(address.get(fieldname) or "")).strip()
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts)


class RestaurantFulfillment(Document):
    def before_insert(self):
        if self.status not in (None, "", "New"):
            frappe.throw(_("A new fulfillment must start in New status"))
        self.status = "New"
        self._set_snapshots(force=True)
        self._append_status_log(None, "New")

    def validate(self):
        self._validate_order_context()
        self._validate_contact()
        self._validate_address()
        self._validate_amounts_and_payment()
        self._validate_status_change()
        self._validate_locked_logistics()
        self._set_snapshots()

    def on_update(self):
        self.publish_update()

    def _validate_order_context(self):
        if self.fulfillment_type not in FULFILLMENT_TRANSITIONS:
            frappe.throw(_("Select Delivery or Pickup"))

        order = frappe.get_doc("Table Order", self.order)
        if order.service_type != self.fulfillment_type:
            frappe.throw(
                _("Order service type {0} does not match fulfillment type {1}").format(
                    order.service_type, self.fulfillment_type
                )
            )
        if order.table:
            frappe.throw(_("Delivery and pickup orders cannot use a restaurant table"))
        if order.status not in {"Attending", "Invoiced"}:
            frappe.throw(_("The restaurant order is not available for fulfillment"))

        self.company = order.company
        self.pos_profile = order.pos_profile
        self.customer = order.customer

    def _validate_contact(self):
        self.contact_phone = str(self.contact_phone or "").strip()
        digits = re.sub(r"\D", "", self.contact_phone)
        if len(digits) < 6 or len(digits) > 20:
            frappe.throw(_("Enter a valid contact phone"))

    def _validate_address(self):
        if self.fulfillment_type == "Delivery":
            if not self.address:
                frappe.throw(_("Select a delivery address"))
            if not address_belongs_to_customer(self.address, self.customer):
                frappe.throw(_("The delivery address must belong to the selected customer"))
        elif self.address:
            frappe.throw(_("Pickup orders do not use a delivery address"))

    def _validate_amounts_and_payment(self):
        self.delivery_fee = flt(self.delivery_fee)
        if self.delivery_fee < 0:
            frappe.throw(_("Delivery fee cannot be negative"))
        if self.fulfillment_type == "Pickup" and self.delivery_fee:
            frappe.throw(_("Pickup orders cannot have a delivery fee"))
        if self.payment_timing == "Cash on Delivery" and not self.expected_payment_method:
            frappe.throw(_("Select the expected payment method for cash on delivery"))

    def _validate_status_change(self):
        previous = self.get_doc_before_save()
        if not previous or previous.status == self.status:
            return
        if not getattr(self, "_transition_in_progress", False):
            frappe.throw(_("Use a fulfillment transition action to change status"))

    def _validate_locked_logistics(self):
        previous = self.get_doc_before_save()
        if not previous or previous.status not in IMMUTABLE_LOGISTICS_STATUSES:
            return
        changed = [field for field in LOGISTICS_FIELDS if self.has_value_changed(field)]
        if changed:
            frappe.throw(_("Delivery details cannot be changed after dispatch or completion"))

    def _set_snapshots(self, force=False):
        previous = self.get_doc_before_save()
        customer_changed = force or not previous or self.has_value_changed("customer")
        address_changed = force or not previous or self.has_value_changed("address")

        if customer_changed or not self.customer_name_snapshot:
            self.customer_name_snapshot = frappe.db.get_value(
                "Customer", self.customer, "customer_name"
            ) or self.customer
        if self.fulfillment_type == "Delivery" and (
            address_changed or not self.address_display_snapshot
        ):
            self.address_display_snapshot = render_address_snapshot(self.address)
        if self.fulfillment_type == "Pickup":
            self.address_display_snapshot = None

    def _append_status_log(self, from_status, to_status, reason=None):
        self.append(
            "status_log",
            {
                "from_status": from_status,
                "to_status": to_status,
                "changed_at": now_datetime(),
                "changed_by": frappe.session.user,
                "reason": reason,
            },
        )

    @frappe.whitelist()
    def transition_status(
        self,
        next_status,
        expected_status=None,
        reason=None,
        courier_name=None,
    ):
        self.check_permission("write")
        return self._transition(
            next_status,
            expected_status=expected_status,
            reason=reason,
            courier_name=courier_name,
        )

    def _transition(
        self,
        next_status,
        expected_status=None,
        reason=None,
        courier_name=None,
        automatic=False,
    ):
        frappe.db.sql(
            "SELECT name FROM `tabRestaurant Fulfillment` WHERE name = %s FOR UPDATE",
            (self.name,),
        )
        self.reload()
        current_status = self.status

        if expected_status and current_status != expected_status:
            frappe.throw(
                _("Fulfillment changed from {0} to {1}; reload and try again").format(
                    expected_status, current_status
                )
            )
        if next_status == current_status:
            return self.board_summary()
        if next_status not in FULFILLMENT_TRANSITIONS[self.fulfillment_type].get(
            current_status, set()
        ):
            frappe.throw(
                _("Invalid fulfillment transition from {0} to {1}").format(
                    current_status, next_status
                )
            )
        if next_status in {"Delivery Failed", "Cancelled"} and not str(reason or "").strip():
            frappe.throw(_("Enter a reason for failure or cancellation"))
        if next_status == "Assigned":
            courier_name = str(courier_name or self.courier_name or "").strip()
            if not courier_name:
                frappe.throw(_("Enter the courier before assigning the delivery"))
            self.courier_name = courier_name

        self._transition_in_progress = True
        self.status = next_status
        self.failure_reason = str(reason or "").strip() or None
        self._append_status_log(current_status, next_status, reason)
        self.save(ignore_permissions=automatic)
        return self.board_summary()

    def board_summary(self):
        order = frappe.db.get_value(
            "Table Order",
            self.order,
            ["amount", "modified"],
            as_dict=True,
        ) or frappe._dict()
        return {
            "name": self.name,
            "order": self.order,
            "fulfillment_type": self.fulfillment_type,
            "status": self.status,
            "customer_name": self.customer_name_snapshot,
            "order_channel": self.order_channel,
            "promised_at": self.promised_at,
            "delivery_fee": flt(self.delivery_fee),
            "courier_name": self.courier_name,
            "payment_timing": self.payment_timing,
            "payment_status": self.payment_status,
            "amount": flt(order.get("amount")),
            "modified": order.get("modified") or self.modified,
        }

    def publish_update(self):
        frappe.publish_realtime(
            "restaurant_fulfillment_update",
            {
                "name": self.name,
                "order": self.order,
                "fulfillment_type": self.fulfillment_type,
                "status": self.status,
            },
            after_commit=True,
        )


def sync_order_preparation(order_name):
    fulfillment_name = frappe.db.get_value(
        "Restaurant Fulfillment", {"order": order_name}, "name"
    )
    if not fulfillment_name:
        return None

    fulfillment = frappe.get_doc("Restaurant Fulfillment", fulfillment_name)
    if fulfillment.status not in {"New", "Preparing", "Ready"}:
        return fulfillment.board_summary()

    fee_item = frappe.db.get_single_value("Restaurant Settings", "delivery_fee_item")
    items = frappe.get_all(
        "Order Entry Item",
        filters={
            "parenttype": "Table Order",
            "parent": order_name,
            "qty": (">", 0),
        },
        fields=["item_code", "status"],
    )
    sent_items = [
        item for item in items
        if item.item_code != fee_item and item.status != "Attending"
    ]
    if not sent_items:
        return fulfillment.board_summary()

    next_status = (
        "Ready"
        if all(item.status in PREPARATION_COMPLETE_STATUSES for item in sent_items)
        else "Preparing"
    )
    if fulfillment.status == next_status:
        return fulfillment.board_summary()

    return fulfillment._transition(
        next_status,
        expected_status=fulfillment.status,
        automatic=True,
    )
