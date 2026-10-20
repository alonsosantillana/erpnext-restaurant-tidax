from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import frappe
from frappe.model.naming import _prompt_autoname

from restaurant_management.setup import install


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
