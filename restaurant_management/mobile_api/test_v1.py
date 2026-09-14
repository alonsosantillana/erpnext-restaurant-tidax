from __future__ import annotations

import json
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import frappe
import yaml

from restaurant_management.mobile_api import v1


class TestRestoTixMobileAPI(unittest.TestCase):
    def setUp(self):
        sites_path = Path(__file__).resolve().parents[4] / "sites"
        frappe.init(site="v15.local", sites_path=str(sites_path), force=True)
        frappe.local.flags.in_test = True

    def tearDown(self):
        frappe.destroy()

    def test_client_request_id_is_normalized(self):
        request_id = uuid.uuid4()

        self.assertEqual(v1._parse_client_request_id(str(request_id).upper()), str(request_id))

    def test_invalid_client_request_id_is_rejected(self):
        with (
            patch.object(v1, "_fail", side_effect=frappe.ValidationError("invalid")) as fail,
            self.assertRaises(frappe.ValidationError),
        ):
            v1._parse_client_request_id("not-a-uuid")

        fail.assert_called_once_with(
            "CLIENT_REQUEST_ID_INVALID", "client_request_id must be a UUID"
        )

    def test_request_hash_is_stable_for_key_order(self):
        first = v1._canonical_hash(
            "mutate_item", "ORDER-1", {"quantity": 2, "item_code": "DISH-1"}
        )
        second = v1._canonical_hash(
            "mutate_item", "ORDER-1", {"item_code": "DISH-1", "quantity": 2}
        )

        self.assertEqual(first, second)

    def test_active_context_rejects_requested_company_mismatch(self):
        with (
            patch.object(v1, "_require_authenticated_user", return_value="waiter@example.com"),
            patch.object(v1, "get_user_restaurant_company", return_value="COMPANY-A"),
            patch.object(
                v1,
                "_fail",
                side_effect=frappe.PermissionError("company not allowed"),
            ) as fail,
            self.assertRaises(frappe.PermissionError),
        ):
            v1._active_context(company="COMPANY-B")

        fail.assert_called_once_with(
            "COMPANY_NOT_ALLOWED",
            "The requested Company is not active for this user",
            403,
            frappe.PermissionError,
        )

    def test_restricted_order_is_visible_to_effective_waiter(self):
        context = frappe._dict(
            user="waiter@example.com",
            settings=frappe._dict(
                restricted_to_owner_order=1,
                restaurant_exceptions=[],
            ),
        )
        order = frappe._dict(
            doctype="Table Order",
            owner="owner@example.com",
            cambio_mozo="waiter@example.com",
        )

        with patch.object(v1.frappe, "has_permission", return_value=True):
            self.assertTrue(v1._restaurant_access_allowed("order", "read", order, context))

    def test_restricted_order_is_hidden_from_other_waiter(self):
        context = frappe._dict(
            user="waiter@example.com",
            settings=frappe._dict(
                restricted_to_owner_order=1,
                restaurant_exceptions=[],
            ),
        )
        order = frappe._dict(
            doctype="Table Order",
            owner="owner@example.com",
            cambio_mozo=None,
        )

        frappe_mock = MagicMock()
        frappe_mock.has_permission.return_value = True
        frappe_mock.db.get_value.return_value = "Waiter"

        with patch.object(v1, "frappe", frappe_mock):
            self.assertFalse(v1._restaurant_access_allowed("order", "read", order, context))

    def test_expected_order_version_accepts_current_version(self):
        modified = datetime(2026, 9, 11, 12, 0, 0, 123456)
        order = frappe._dict(name="ORDER-1")

        with patch.object(v1, "_latest_order_modified", return_value=modified):
            version = v1._rfc3339(modified)
            v1._assert_order_version(order, version)

        self.assertRegex(version, r"[+-][0-9]{2}:[0-9]{2}$")

    def test_expected_order_version_rejects_stale_version(self):
        order = frappe._dict(name="ORDER-1")
        current_order = {"name": "ORDER-1", "status": "Attending"}
        with (
            patch.object(
                v1,
                "_latest_order_modified",
                return_value=datetime(2026, 9, 11, 12, 1),
            ),
            patch.object(
                v1,
                "_fail",
                side_effect=frappe.ValidationError("conflict"),
            ) as fail,
            patch.object(v1, "_order_payload", return_value=current_order),
            patch.object(v1, "_order_version", return_value="2026-09-11T12:01:00-05:00"),
            self.assertRaises(frappe.ValidationError),
        ):
            v1._assert_order_version(order, "2026-09-11T12:00:00")

        fail.assert_called_once_with(
            "ORDER_VERSION_CONFLICT",
            "The order changed in another session",
            409,
            details={
                "current_order": current_order,
                "current_order_version": "2026-09-11T12:01:00-05:00",
            },
        )

    def test_cached_item_mutation_does_not_lock_or_repeat_order_change(self):
        cached = {"api_version": "1.0", "data": {"name": "ORDER-1"}}
        context = frappe._dict(company="COMPANY-A", pos_profile="POS-A")

        with (
            patch.object(v1, "_active_context", return_value=context),
            patch.object(v1, "_begin_request", return_value=(MagicMock(), cached)),
            patch.object(v1, "_lock_order") as lock_order,
        ):
            result = v1.mutate_item(
                order_name="ORDER-1",
                action="set_note",
                client_request_id=str(uuid.uuid4()),
                expected_order_version="2026-09-11T12:00:00",
                identifier="ITEM-1",
                notes="Sin cebolla",
            )

        self.assertEqual(result, cached)
        lock_order.assert_not_called()

    def test_new_item_must_exist_in_authorized_pos_catalog(self):
        context = frappe._dict(
            pos_profile="POS-A",
            profile=frappe._dict(selling_price_list="Retail"),
        )

        with (
            patch.object(v1, "get_restaurant_items", return_value={"items": []}),
            patch.object(
                v1,
                "_fail",
                side_effect=frappe.DoesNotExistError("not available"),
            ) as fail,
            self.assertRaises(frappe.DoesNotExistError),
        ):
            v1._new_item_entry(context, "DISH-X", 1, "", "rtx-id")

        fail.assert_called_once_with(
            "ITEM_NOT_AVAILABLE",
            "The requested item is not available in this POS Profile",
            404,
        )

    def test_new_item_uses_authoritative_catalog_price_and_tax(self):
        context = frappe._dict(
            pos_profile="POS-A",
            profile=frappe._dict(selling_price_list="Retail"),
        )
        catalog_item = frappe._dict(
            item_code="DISH-1",
            price_list_rate=18.5,
            item_tax_template="IGV",
            item_tax_rate='{"IGV - T": 18}',
        )
        item = frappe._dict(
            name="DISH-1",
            item_name="Dish",
            stock_uom="Nos",
            disabled=0,
            is_sales_item=1,
            has_batch_no=0,
            has_serial_no=0,
        )

        frappe_mock = MagicMock()
        frappe_mock.db.get_value.return_value = item

        with (
            patch.object(v1, "get_restaurant_items", return_value={"items": [catalog_item]}),
            patch.object(v1, "frappe", frappe_mock),
        ):
            entry = v1._new_item_entry(context, "DISH-1", 2, "Hot", "rtx-id")

        self.assertEqual(entry["price_list_rate"], 18.5)
        self.assertEqual(entry["rate"], 18.5)
        self.assertEqual(entry["item_tax_template"], "IGV")
        self.assertEqual(entry["item_tax_rate"], '{"IGV - T": 18}')

    def test_new_item_rejects_missing_pos_price_with_stable_error(self):
        context = frappe._dict(
            pos_profile="POS-A",
            profile=frappe._dict(selling_price_list="Retail"),
        )
        catalog_item = frappe._dict(
            item_code="DISH-1",
            price_list_rate=0,
            rate=0,
        )
        item = frappe._dict(
            name="DISH-1",
            item_name="Dish",
            stock_uom="Nos",
            disabled=0,
            is_sales_item=1,
            has_batch_no=0,
            has_serial_no=0,
        )
        frappe_mock = MagicMock()
        frappe_mock.db.get_value.return_value = item

        with (
            patch.object(v1, "get_restaurant_items", return_value={"items": [catalog_item]}),
            patch.object(v1, "frappe", frappe_mock),
            patch.object(
                v1,
                "_fail",
                side_effect=frappe.ValidationError("missing price"),
            ) as fail,
            self.assertRaises(frappe.ValidationError),
        ):
            v1._new_item_entry(context, "DISH-1", 1, "", "rtx-id")

        fail.assert_called_once_with(
            "ITEM_PRICE_MISSING",
            "The requested item has no price configured in the POS price list",
            409,
        )

    def test_send_command_evaluates_table_order_send_property_once(self):
        class FakeOrder:
            name = "ORDER-1"
            entry_items = [frappe._dict(status=v1.ITEM_STATUS_UNSENT)]

            def __init__(self):
                self.send_reads = 0
                self.reloads = 0

            @property
            def send(self):
                self.send_reads += 1
                return {"name": self.name}

            def reload(self):
                self.reloads += 1
                return self

        order = FakeOrder()
        context = frappe._dict(company="COMPANY-A", pos_profile="POS-A")
        response = {"api_version": "1.0", "data": {"name": "ORDER-1"}}

        with (
            patch.object(v1, "_active_context", return_value=context),
            patch.object(v1, "_begin_request", return_value=(MagicMock(), None)),
            patch.object(v1, "_lock_order", return_value=order),
            patch.object(v1, "_validate_order_access"),
            patch.object(v1, "_assert_order_version"),
            patch.object(v1, "_order_payload", return_value={"name": "ORDER-1"}),
            patch.object(v1, "_envelope", return_value=response),
            patch.object(v1, "_complete_request") as complete_request,
        ):
            result = v1.send_command(
                order_name="ORDER-1",
                client_request_id=str(uuid.uuid4()),
                expected_order_version="2026-09-11T12:00:00-05:00",
            )

        self.assertEqual(result, response)
        self.assertEqual(order.send_reads, 1)
        self.assertEqual(order.reloads, 1)
        complete_request.assert_called_once()

    def test_table_payload_does_not_expose_assigned_user(self):
        context = frappe._dict(
            user="waiter@example.com",
            company="COMPANY-A",
            pos_profile="POS-A",
        )
        room = frappe._dict(name="ROOM-1", description="Main")
        table = frappe._dict(
            name="TABLE-1",
            description="Table 1",
            room="ROOM-1",
            no_of_seats=4,
            color="#fff",
            shape="Round",
            current_user="other@example.com",
        )

        with (
            patch.object(v1, "_active_context", return_value=context),
            patch.object(v1, "_allowed_rooms", return_value=["ROOM-1"]),
            patch.object(v1.frappe, "get_all", side_effect=[[room], [table], []]),
        ):
            result = v1.get_tables()

        table_payload = result["data"]["tables"][0]
        self.assertNotIn("current_user", table_payload)
        self.assertFalse(table_payload["occupied_by_me"])

    def test_openapi_contract_contains_only_mvp_routes(self):
        contract_path = Path(__file__).resolve().parents[2] / "docs" / "openapi" / "resto-tix-v1.yaml"
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        paths = set(contract["paths"])

        self.assertEqual(contract["openapi"], "3.1.0")
        self.assertEqual(
            paths,
            {
                "/api/v1/context",
                "/api/v1/tables",
                "/api/v1/catalog",
                "/api/v1/orders/{order_name}",
                "/api/v1/orders/open",
                "/api/v1/orders/{order_name}/items",
                "/api/v1/orders/{order_name}/commands",
                "/api/v1/changes",
            },
        )
        self.assertFalse(any("payment" in path or "invoice" in path for path in paths))
        self.assertFalse(
            contract["components"]["schemas"]["MutateItemRequest"]["unevaluatedProperties"]
        )

        pending = [contract]
        references = []
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                references.extend(
                    item for key, item in value.items() if key == "$ref" and isinstance(item, str)
                )
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        for reference in references:
            self.assertTrue(reference.startswith("#/"))
            target = contract
            for part in reference[2:].split("/"):
                target = target[part]

    def test_idempotency_doctype_has_unique_internal_key_and_private_permissions(self):
        doctype_path = (
            Path(__file__).resolve().parents[1]
            / "restaurant_management"
            / "doctype"
            / "restaurant_mobile_request"
            / "restaurant_mobile_request.json"
        )
        metadata = json.loads(doctype_path.read_text(encoding="utf-8"))
        fields = {field["fieldname"]: field for field in metadata["fields"]}

        self.assertEqual(metadata["autoname"], "field:request_key")
        self.assertEqual(fields["request_key"]["unique"], 1)
        self.assertEqual(
            {permission["role"] for permission in metadata["permissions"]},
            {"System Manager"},
        )

    def test_mobile_facade_contains_no_manual_database_commit(self):
        source_path = Path(v1.__file__)
        source = source_path.read_text(encoding="utf-8")

        self.assertNotIn("frappe.db.commit(", source)

    def test_mobile_facade_enforces_http_methods(self):
        allowed = frappe.allowed_http_methods_for_whitelisted_func
        for function in (
            v1.get_context,
            v1.get_tables,
            v1.get_catalog,
            v1.get_order,
            v1.get_changes,
        ):
            self.assertEqual(allowed[function], ["GET"])
        for function in (v1.open_order, v1.mutate_item, v1.send_command):
            self.assertEqual(allowed[function], ["POST"])


if __name__ == "__main__":
    unittest.main()
