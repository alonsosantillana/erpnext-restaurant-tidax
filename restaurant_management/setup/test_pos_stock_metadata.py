"""Pure metadata compatibility tests: no site, invoice writes, DDL or providers."""
import ast
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from restaurant_management.setup import pos_stock_metadata as compat

NATIVE = {"fieldname": "update_stock", "fieldtype": "Check", "default": "0", "label": "Update Stock", "print_hide": 1}
SCHEMA = {
    "label": {"fieldtype": "Data"}, "description": {"fieldtype": "Small Text"},
    "default": {"fieldtype": "Small Text"},
    **{name: {"fieldtype": "Check", "default": "0"} for name in ["read_only", "no_copy", "in_standard_filter", "print_hide", "hidden", "allow_on_submit"]},
}
LEGACY = {"name": "POS Invoice-update_stock", "dt": "POS Invoice", "fieldname": "update_stock", "fieldtype": "Check", "default": "0", "label": "Actualiza inventario", "description": "Existing stock indicator", "read_only": 1, "no_copy": 1, "in_standard_filter": 1, "print_hide": 0, "insert_after": "restaurant_pos_opening_entry"}


class TestNativePOSStockMetadata(TestCase):
    def setUp(self):
        self.custom = [copy.deepcopy(LEGACY)]
        self.standard = [{"fieldtype": "Check"}]
        self.setters = []
        self.snapshot = self.enterContext(patch.object(compat, "_snapshot", return_value="private-metadata-evidence"))
        self.enterContext(patch.object(compat, "_source_metadata", return_value=(dict(NATIVE), dict(SCHEMA))))
        self.enterContext(patch.object(compat.frappe, "get_all", side_effect=self.get_all))
        self.db = SimpleNamespace(has_column=Mock(return_value=True))
        self.enterContext(patch.object(compat.frappe, "db", self.db))
        self.enterContext(patch.object(compat.frappe, "throw", side_effect=lambda message: (_ for _ in ()).throw(ValueError(message))))
        self.create = self.enterContext(patch.object(compat, "make_property_setter", side_effect=self.make_setter))
        self.remove = self.enterContext(patch.object(compat, "delete_custom_fields", side_effect=self.delete_custom))

    def get_all(self, doctype, **kwargs):
        return {"DocField": self.standard, "Custom Field": self.custom, "Property Setter": self.setters}[doctype]

    def make_setter(self, dt, field, property_name, value, property_type, **kwargs):
        self.setters.append(dict(doctype_or_field="DocField", doc_type=dt, field_name=field, property=property_name, value=value, property_type=property_type))

    def delete_custom(self, definition, **kwargs):
        self.assertEqual(definition, {"POS Invoice": ["update_stock"]})
        self.assertEqual(kwargs, {"bypass_hooks": True})
        self.custom.clear()

    def test_adopts_native_with_same_default_and_preserved_presentation(self):
        result = compat.adopt_native_stock_field()
        self.assertTrue(result["removed_duplicate"])
        values = {row["property"]: row["value"] for row in self.setters}
        self.assertEqual(values, {"label": "Actualiza inventario", "description": "Existing stock indicator", "read_only": 1, "no_copy": 1, "in_standard_filter": 1, "print_hide": 0})
        self.assertNotIn("default", values)
        self.assertNotIn("insert_after", values)
        self.remove.assert_called_once()

    def test_existing_field_and_global_order_setters_are_not_replaced(self):
        self.setters = [dict(doctype_or_field="DocField", field_name="update_stock", property="read_only", value="0", property_type="Check"), dict(doctype_or_field="DocType", property="field_order", value='["name","update_stock"]')]
        before = copy.deepcopy(self.setters)
        compat.adopt_native_stock_field()
        self.assertEqual(self.setters[:2], before)
        self.assertNotIn("read_only", [call.args[2] for call in self.create.call_args_list])
        self.assertNotIn("field_order", [call.args[2] for call in self.create.call_args_list])

    def test_native_property_types_are_used_and_validation_does_not_run_ddl(self):
        compat.adopt_native_stock_field()
        calls = {call.args[2]: call for call in self.create.call_args_list}
        self.assertEqual(calls["description"].args[4], "Small Text")
        self.assertEqual(calls["label"].args[4], "Data")
        self.assertTrue(all(call.kwargs == {"validate_fields_for_doctype": False} for call in calls.values()))

    def test_snapshot_precedes_every_metadata_mutation(self):
        events = []
        self.snapshot.side_effect = lambda *args: events.append("snapshot") or "private"
        self.create.side_effect = lambda *args, **kwargs: events.append("setter")
        self.remove.side_effect = lambda *args, **kwargs: events.append("delete")
        compat.adopt_native_stock_field()
        self.assertEqual(events[0], "snapshot")
        self.assertEqual(events[-1], "delete")

    def test_repeat_migration_and_setup_are_idempotent(self):
        compat.adopt_native_stock_field()
        created = self.create.call_count
        self.assertFalse(compat.adopt_native_stock_field()["changed"])
        self.assertFalse(compat.adopt_native_stock_field(properties=LEGACY, apply_definition=True)["changed"])
        self.assertEqual(self.create.call_count, created)
        self.remove.assert_called_once()
        self.snapshot.assert_called_once()

    def test_native_without_duplicate_migration_is_noop(self):
        self.custom = []
        self.assertFalse(compat.before_migrate()["changed"])
        self.snapshot.assert_not_called()
        self.create.assert_not_called()

    def test_setup_uses_native_field_without_creating_custom_field(self):
        self.custom = []
        result = compat.adopt_native_stock_field(properties=LEGACY, apply_definition=True)
        self.assertTrue(result["native"])
        self.remove.assert_not_called()

    def test_legacy_core_without_native_preserves_old_path(self):
        with patch.object(compat, "_source_metadata", return_value=(None, {})):
            self.assertEqual(compat.adopt_native_stock_field(), {"native": False, "changed": False})
        self.remove.assert_not_called()
        self.snapshot.assert_not_called()

    def test_missing_column_fails_before_mutation(self):
        self.db.has_column.return_value = False
        with self.assertRaises(ValueError): compat.adopt_native_stock_field()
        self.snapshot.assert_not_called()
        self.remove.assert_not_called()

    def test_wrong_standard_custom_virtual_or_multiple_field_fails_closed(self):
        for standard, custom in [([], [LEGACY]), ([{"fieldtype": "Int"}], [LEGACY]), ([{"fieldtype": "Check"}], [{**LEGACY, "fieldtype": "Int"}]), ([{"fieldtype": "Check"}], [{**LEGACY, "is_virtual": 1}]), ([{"fieldtype": "Check"}], [LEGACY, LEGACY])]:
            with self.subTest(standard=standard):
                self.standard, self.custom = standard, custom
                with self.assertRaises(ValueError): compat.adopt_native_stock_field()
        self.snapshot.assert_not_called()
        self.remove.assert_not_called()

    def test_financial_default_change_requires_review(self):
        self.custom[0]["default"] = "1"
        with self.assertRaisesRegex(ValueError, "policy review"): compat.adopt_native_stock_field()
        self.snapshot.assert_not_called()
        self.remove.assert_not_called()

    def test_storage_attribute_change_fails_before_mutation(self):
        self.custom[0]["unique"] = 1
        with self.assertRaises(ValueError): compat.adopt_native_stock_field()
        self.snapshot.assert_not_called()
        self.remove.assert_not_called()

    def test_incompatible_fieldtype_property_setter_fails_closed(self):
        self.setters = [dict(doctype_or_field="DocField", field_name="update_stock", property="fieldtype", value="Int")]
        with self.assertRaises(ValueError): compat.adopt_native_stock_field()
        self.snapshot.assert_not_called()

    def test_source_contains_no_invoice_ddl_delete_doc_or_commit_path(self):
        tree = ast.parse(Path(compat.__file__).read_text())
        forbidden = {"sql", "sql_ddl", "updatedb", "delete_doc", "commit", "on_trash", "save", "submit", "cancel", "enqueue", "sendmail"}
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & forbidden)

    def test_source_native_definition_and_installer_guard_contract(self):
        native, schema = compat._source_metadata.__wrapped__() if hasattr(compat._source_metadata, "__wrapped__") else (NATIVE, SCHEMA)
        self.assertEqual(native["fieldtype"], "Check")
        root = Path(compat.__file__).parents[1]
        install = (root / "setup/install.py").read_text()
        self.assertIn('field_name == "update_stock"', install)
        self.assertIn("adopt_native_stock_field", install)
        hooks = (root / "hooks.py").read_text()
        self.assertIn("restaurant_management.setup.pos_stock_metadata.before_migrate", hooks)

    def test_snapshot_directory_is_private_and_inside_workia(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary) / "site"
            site.mkdir(mode=0o700)
            with patch.object(compat.frappe, "get_site_path", return_value=str(site / "WorkIA")):
                folder = compat._snapshot_directory()
            self.assertTrue(folder.is_relative_to(site / "WorkIA"))
            self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
            self.assertEqual((site / "WorkIA").stat().st_mode & 0o777, 0o700)

    def test_snapshot_directory_rejects_symlink_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary) / "site"
            site.mkdir(mode=0o700)
            workia = site / "WorkIA"
            workia.mkdir(mode=0o700)
            outside = Path(temporary) / "outside"
            outside.mkdir(mode=0o700)
            (workia / "native_pos_stock_metadata_compat_v16").symlink_to(outside, target_is_directory=True)
            with patch.object(compat.frappe, "get_site_path", return_value=str(workia)):
                with self.assertRaisesRegex(ValueError, "symlinks"):
                    compat._snapshot_directory()
            self.assertEqual(list(outside.iterdir()), [])

    def test_real_setup_function_skips_native_custom_field_creation(self):
        source = Path(compat.__file__).with_name("install.py")
        tree = ast.parse(source.read_text())
        method = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "set_custom_fields")
        framework = SimpleNamespace(db=SimpleNamespace(exists=Mock()), new_doc=Mock(), get_doc=Mock())
        scope = {"frappe": framework, "docs": {"POS Invoice": {"update_stock": dict(LEGACY)}}, "fields_not_needed": [], "_reorder_custom_fields": Mock()}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "real-setup-function", "exec"), scope)
        with patch.object(compat, "adopt_native_stock_field", return_value={"native": True}) as adoption:
            scope["set_custom_fields"]()
        adoption.assert_called_once()
        framework.db.exists.assert_not_called()
        framework.new_doc.assert_not_called()
        framework.get_doc.assert_not_called()
