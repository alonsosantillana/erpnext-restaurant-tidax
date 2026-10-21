from copy import deepcopy
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import frappe
from frappe.model.naming import _prompt_autoname

from restaurant_management.setup import install


class TestKitchenProfilePermissions(TestCase):
    def setUp(self):
        self.rules = {}
        self.db = self.enterContext(patch.object(install.frappe, "db", MagicMock()))
        self.db.exists.return_value = True
        self.db.get_value.side_effect = self.get_permission
        self.add = self.enterContext(
            patch("frappe.permissions.add_permission", side_effect=self.add_permission)
        )
        self.update = self.enterContext(
            patch(
                "frappe.permissions.update_permission_property",
                side_effect=self.update_permission,
            )
        )
        self.enterContext(patch.object(install.frappe, "clear_cache"))
        self.enterContext(patch.object(install, "set_production_report_permissions"))

    def get_permission(self, doctype, identifier, fieldname=None):
        self.assertEqual(doctype, "Custom DocPerm")
        if isinstance(identifier, dict):
            key = (
                identifier["parent"], identifier["role"],
                identifier["permlevel"], identifier["if_owner"],
            )
            return self.rules.get(key, {}).get("name")
        return next(
            (row.get(fieldname, 0) for row in self.rules.values() if row["name"] == identifier),
            None,
        )

    def add_permission(self, doctype, role, permlevel=0, ptype=None):
        key = (doctype, role, permlevel, 0)
        self.assertNotIn(key, self.rules)
        self.rules[key] = {"name": f"perm-{len(self.rules)}", ptype: 1}

    def update_permission(self, doctype, role, permlevel, ptype, value):
        self.rules[(doctype, role, permlevel, 0)][ptype] = value

    def test_kitchen_receives_only_profile_and_company_read_select(self):
        install.set_operational_role_permissions()

        kitchen_rules = {
            key[0]: {field: value for field, value in row.items() if field != "name"}
            for key, row in self.rules.items() if key[1] == "resto_cocina"
        }
        self.assertEqual(kitchen_rules, {
            "Company": {"read": 1, "select": 1},
            "POS Profile": {"read": 1, "select": 1},
        })
        self.add.assert_any_call("POS Profile", "resto_cocina", permlevel=0, ptype="read")

    def test_existing_rule_is_repaired_and_custom_grants_are_preserved(self):
        key = ("POS Profile", "resto_cocina", 0, 0)
        self.rules[key] = {"name": "existing-kitchen-rule", "read": 1, "write": 1}

        install.set_operational_role_permissions()

        self.assertEqual(self.rules[key], {
            "name": "existing-kitchen-rule", "read": 1, "write": 1, "select": 1,
        })
        kitchen_updates = [
            invocation for invocation in self.update.call_args_list
            if invocation.args[:2] == ("POS Profile", "resto_cocina")
        ]
        self.assertEqual(kitchen_updates, [call("POS Profile", "resto_cocina", 0, "select", 1)])
        self.assertFalse(any(
            invocation.args[:2] == ("POS Profile", "resto_cocina")
            for invocation in self.add.call_args_list
        ))

    def test_repeated_sync_creates_no_duplicates_or_rewrites(self):
        install.set_operational_role_permissions()
        before = deepcopy(self.rules)
        self.add.reset_mock()
        self.update.reset_mock()

        install.set_operational_role_permissions()

        self.assertIn(("POS Profile", "resto_cocina", 0, 0), self.rules)
        self.assertEqual(self.rules, before)
        self.add.assert_not_called()
        self.update.assert_not_called()


class TestRoomPermissionsClientScript(TestCase):
    def setUp(self):
        self.persisted = False
        self.values = {}
        self.document = MagicMock()
        self.document.name = None
        self.document.set.side_effect = self.values.__setitem__
        self.document.is_new.side_effect = lambda: not self.persisted
        self.document.insert.side_effect = self.insert_script

        self.db = self.enterContext(patch.object(install.frappe, "db", MagicMock()))
        self.db.get_value.side_effect = self.find_script
        self.new_doc = self.enterContext(
            patch.object(install.frappe, "new_doc", return_value=self.document)
        )
        self.get_doc = self.enterContext(
            patch.object(install.frappe, "get_doc", return_value=self.document)
        )
        self.get_all = self.enterContext(
            patch.object(install.frappe, "get_all", return_value=[])
        )
        self.enterContext(
            patch.object(
                install.frappe,
                "throw",
                side_effect=frappe.ValidationError("Please set the document name"),
            )
        )
        self.enterContext(
            patch("frappe.model.naming._", side_effect=lambda message: message)
        )

    def find_script(self, doctype, filters, fieldname):
        self.assertEqual(doctype, "Client Script")
        self.assertEqual(fieldname, "name")
        if (
            self.persisted
            and self.values.get("dt") == filters["dt"]
            and self.values.get("view") == filters["view"]
            and filters["script"][1].strip("%") in self.values.get("script", "")
        ):
            return self.document.name
        return None

    def insert_script(self):
        # Exercise Frappe's actual Prompt check without a database or site.
        _prompt_autoname("Prompt", self.document)
        self.persisted = True

    def use_existing_script(self):
        self.persisted = True
        self.document.name = "Existing room access script"
        self.values.update(
            dt="POS Profile", view="Form", script="get_room_permissions"
        )

    def test_new_script_has_a_name_before_prompt_validation(self):
        install.set_custom_scripts()

        self.assertEqual(
            self.document.name, "Restaurant POS Profile Room Permissions"
        )
        self.assertEqual(self.values["dt"], "POS Profile")
        self.assertEqual(self.values["view"], "Form")
        self.assertEqual(self.values["enabled"], 1)
        self.assertIn("get_room_permissions", self.values["script"])
        self.document.insert.assert_called_once_with()
        self.document.save.assert_not_called()

    def test_existing_matching_script_keeps_its_name(self):
        self.use_existing_script()

        install.set_custom_scripts()

        self.assertEqual(self.document.name, "Existing room access script")
        self.get_doc.assert_called_once_with(
            "Client Script", "Existing room access script"
        )
        self.new_doc.assert_not_called()
        self.document.insert.assert_not_called()
        self.document.save.assert_called_once_with()

    def test_repeat_run_saves_the_script_created_on_first_run(self):
        install.set_custom_scripts()
        install.set_custom_scripts()

        self.new_doc.assert_called_once_with("Client Script")
        self.get_doc.assert_called_once_with(
            "Client Script", "Restaurant POS Profile Room Permissions"
        )
        self.document.insert.assert_called_once_with()
        self.document.save.assert_called_once_with()

    def test_only_matching_legacy_scripts_are_disabled(self):
        self.use_existing_script()
        self.get_all.return_value = ["Legacy room script"]

        install.set_custom_scripts()

        self.get_all.assert_called_once_with(
            "Client Script",
            filters={
                "dt": "POS Profile",
                "view": "Form",
                "script": ["like", "%new DeskForm%"],
            },
            pluck="name",
        )
        self.assertEqual(
            self.db.set_value.call_args_list,
            [
                call(
                    "Client Script", "Legacy room script", "enabled", 0,
                    update_modified=False,
                )
            ],
        )
