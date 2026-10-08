import ast
import unittest
from pathlib import Path

import app
import client
import client_features


class HistoryRemovalTests(unittest.TestCase):
    def test_browser_history_endpoints_are_removed(self):
        paths = {route.path for route in app.app.routes if hasattr(route, "path")}

        self.assertFalse(any("history" in path.lower() and path != "/api/raw-history" for path in paths))
        self.assertNotIn("/api/website-history", paths)
        self.assertNotIn("/api/visited-links", paths)

    def test_client_package_preserves_public_entry_points(self):
        self.assertTrue(callable(client.run_client))
        self.assertTrue(callable(client.start_keyboard_listener))
        self.assertTrue(callable(client.main))
        self.assertTrue(callable(client_features.main))

        client_source = Path("client_features/core.py").read_text(encoding="utf-8")
        tree = ast.parse(client_source)
        function_names = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        removed_functions = {
            "browser_history_paths",
            "collect_browser_history_entries",
            "sync_browser_history",
            "post_website_history",
            "website_history_sender",
        }
        self.assertFalse(removed_functions.intersection(function_names))
        self.assertIn("get_browser_url", function_names)
        self.assertIn("get_message_source_url", function_names)
        self.assertIn("run_client", function_names)
