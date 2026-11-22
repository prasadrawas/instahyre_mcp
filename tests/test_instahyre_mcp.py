"""
Unit tests for instahyre_mcp server, auth resolution, TTL cache, and client methods.
"""
import sys
from pathlib import Path

workspace_dir = str(Path(__file__).resolve().parent.parent.parent)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import unittest
from instahyre_mcp.server import mcp
from instahyre_mcp import auth
from instahyre_mcp.cache import TTLCache


class TestInstahyreMCP(unittest.TestCase):
    """Unit test suite for Instahyre MCP components."""

    def test_mcp_initialization(self):
        """Verify FastMCP server name and exact 6-tool registration."""
        self.assertEqual(mcp.name, "instahyre-mcp")
        self.assertEqual(len(mcp._tool_manager._tools), 6)

    def test_tool_names(self):
        """Confirm all 6 unified tools exist."""
        tools = mcp._tool_manager._tools
        expected_tools = [
            "manage_profile",
            "search_jobs",
            "get_job_details",
            "manage_job_pipeline",
            "manage_account",
            "manage_session",
        ]
        self.assertEqual(len(tools), 6)
        for tool_name in expected_tools:
            self.assertIn(tool_name, tools, f"Missing tool: {tool_name}")

    def test_ttl_cache(self):
        """Test TTLCache set, get, expiration, and invalidation."""
        cache = TTLCache(default_ttl=10, max_size=5)
        cache.set("key1", "val1")
        self.assertEqual(cache.get("key1"), "val1")

        # Expiration test
        cache.set("short_key", "short_val", ttl=-1)
        self.assertIsNone(cache.get("short_key"))

        # Invalidation test
        cache.set("prefix_a", "val_a")
        cache.set("prefix_b", "val_b")
        cache.set("other", "val_other")
        cache.invalidate("prefix_")
        self.assertIsNone(cache.get("prefix_a"))
        self.assertIsNone(cache.get("prefix_b"))
        self.assertEqual(cache.get("other"), "val_other")

    def test_build_cookie_header(self):
        """Test Cookie header formatting."""
        header = auth.build_cookie_header("sess123", "csrf456", "cf789")
        self.assertIn("sessionid=sess123", header)
        self.assertIn("csrftoken=csrf456", header)
        self.assertIn("cf_clearance=cf789", header)

    def test_manage_profile_parameter_validation(self):
        """manage_profile requires file for upload and details for update."""
        from instahyre_mcp import server

        res_upload = server.manage_profile(action="upload_resume")
        self.assertEqual(res_upload.get("status_code"), 400)
        self.assertIn("resume_file_path is required", res_upload.get("error", ""))

        res_update = server.manage_profile(action="update")
        self.assertEqual(res_update.get("status_code"), 400)
        self.assertIn("personal", res_update.get("error", ""))

    def test_manage_pipeline_parameter_validation(self):
        """manage_job_pipeline requires job_id for apply/pass."""
        from instahyre_mcp import server

        res_apply = server.manage_job_pipeline(action="apply")
        self.assertEqual(res_apply.get("status_code"), 400)
        self.assertIn("job_id is required", res_apply.get("error", ""))

        res_pass = server.manage_job_pipeline(action="pass")
        self.assertEqual(res_pass.get("status_code"), 400)
        self.assertIn("job_id is required", res_pass.get("error", ""))

        res_bulk = server.manage_job_pipeline(action="apply_bulk")
        self.assertEqual(res_bulk.get("status_code"), 400)
        self.assertIn("job_ids list is required", res_bulk.get("error", ""))

    def test_manage_account_parameter_validation(self):
        """manage_account requires company_name for block/unblock."""
        from instahyre_mcp import server

        res_block = server.manage_account(action="block_company")
        self.assertEqual(res_block.get("status_code"), 400)
        self.assertIn("company_name is required", res_block.get("error", ""))

        res_unblock = server.manage_account(action="unblock_company")
        self.assertEqual(res_unblock.get("status_code"), 400)
        self.assertIn("company_name is required", res_unblock.get("error", ""))


if __name__ == "__main__":
    unittest.main()
