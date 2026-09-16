from pathlib import Path
import re
import unittest


APP_ROOT = Path(__file__).resolve().parent
ORDER_MANAGE_JS = APP_ROOT / "public" / "restaurant" / "js" / "order-manage-class.js"
ORDER_ITEMS_CSS = APP_ROOT / "public" / "restaurant" / "css" / "order-items-container.css"


class TestOrderPanelLayout(unittest.TestCase):
    def test_side_panel_wraps_items_editor_and_controls(self):
        source = ORDER_MANAGE_JS.read_text(encoding="utf-8")

        wrapper = source.index('class="order-side-panel"')
        items = source.index('class="panel-order-items"', wrapper)
        editor = source.index("panel-order-edit", items)
        controls = source.index("order-manage-control-buttons", editor)

        self.assertLess(wrapper, items)
        self.assertLess(items, editor)
        self.assertLess(editor, controls)

    def test_only_item_region_uses_remaining_height_and_scrolls(self):
        css = ORDER_ITEMS_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            css,
            re.compile(
                r"\.order-side-panel\s*\{[^}]*position:\s*absolute;"
                r"[^}]*inset:\s*0;"
                r"[^}]*display:\s*flex;"
                r"[^}]*flex-direction:\s*column;"
                r"[^}]*height:\s*100%;"
                r"[^}]*min-height:\s*0;",
                re.DOTALL,
            ),
        )
        self.assertRegex(
            css,
            re.compile(
                r"\.panel-order-items\s*\{[^}]*flex:\s*1 1 auto;"
                r"[^}]*min-height:\s*0;"
                r"[^}]*overflow-y:\s*auto;",
                re.DOTALL,
            ),
        )
        self.assertIn("flex: 0 0 65px;", css)
        self.assertIn("flex: 0 0 265px;", css)


if __name__ == "__main__":
    unittest.main()
