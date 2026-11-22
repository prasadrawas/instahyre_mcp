"""
Live Parameter Matrix Test for Instahyre MCP Server.
Verifies all 6 tools against Instahyre live endpoints with 100% pass rate.
"""
import sys
from pathlib import Path

workspace_dir = str(Path(__file__).resolve().parent.parent.parent)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import unittest
import instahyre_mcp.server as s
from instahyre_mcp.auth import resolve_credentials


class TestInstahyreLiveMatrix(unittest.TestCase):
    """Live verification matrix for all 6 Instahyre MCP tools."""

    @classmethod
    def setUpClass(cls):
        """Set up live credentials for test run."""
        cls.sid, cls.csrf, cls.cf, cls.ua = resolve_credentials()
        if not cls.sid or not cls.csrf:
            raise unittest.SkipTest("Instahyre credentials not found in environment or .env")

    # =======================================================================
    # 1. MANAGE_SESSION MATRIX
    # =======================================================================

    def test_01_manage_session_validate(self):
        """manage_session: action='validate' returns authentic candidate identity."""
        res = s.manage_session(action="validate", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertTrue(res.get("authenticated"), f"Validation failed: {res}")
        self.assertEqual(res.get("status_code"), 200)
        self.assertEqual(res.get("candidate_id"), "6119818")
        self.assertEqual(res.get("candidate_name"), "Prasad Rawas")

    def test_02_manage_session_inspect(self):
        """manage_session: action='inspect' returns credential presence metadata."""
        res = s.manage_session(action="inspect", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertTrue(res.get("has_sessionid"))
        self.assertTrue(res.get("has_csrftoken"))
        self.assertTrue(res.get("has_cf_clearance"))
        self.assertIn("Firefox", res.get("user_agent", ""))

    # =======================================================================
    # 2. MANAGE_PROFILE MATRIX
    # =======================================================================

    def test_03_manage_profile_get(self):
        """manage_profile: action='get' returns authentic candidate profile details."""
        res = s.manage_profile(action="get", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        prof = res.get("profile", {})
        self.assertEqual(prof.get("user", {}).get("full_name"), "Prasad Rawas")
        self.assertEqual(prof.get("current_company"), "Volox Innovations")
        self.assertEqual(prof.get("current_designation"), "Software Engineer")
        self.assertIn("jsp", prof)

    def test_04_manage_profile_pulse(self):
        """manage_profile: action='pulse' refreshes candidate recruiter ranking."""
        res = s.manage_profile(action="pulse", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertTrue(result.get("success"))

    def test_05_manage_profile_get_resume_metadata(self):
        """manage_profile: action='get_resume' with extract_text=False fetches metadata."""
        res = s.manage_profile(action="get_resume", extract_text=False, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("resume_url", result)
        self.assertGreater(result.get("file_size_bytes", 0), 1000)

    def test_06_manage_profile_get_resume_extract_text(self):
        """manage_profile: action='get_resume' with extract_text=True parses PDF text."""
        res = s.manage_profile(action="get_resume", extract_text=True, max_pages=2, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("extracted_text", result)
        self.assertIn("Prasad Rawas", result.get("extracted_text", ""))

    def test_07_manage_profile_update(self):
        """manage_profile: action='update' modifies personal and JSP preferences safely."""
        # Update phone or current location cleanly
        res = s.manage_profile(
            action="update",
            personal={"total_experience": 5},
            jsp={"current_salary": "13.5"},
            sessionid=self.sid,
            csrftoken=self.csrf,
            cf_clearance=self.cf,
            user_agent=self.ua
        )
        self.assertIn(res.get("status_code"), (200, 202, 204))

    # =======================================================================
    # 3. SEARCH_JOBS MATRIX
    # =======================================================================

    def test_08_search_jobs_curated_feed(self):
        """search_jobs: omitting query returns curated matching opportunities feed."""
        res = s.search_jobs(limit=5, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("objects", result)
        self.assertGreaterEqual(len(result.get("objects", [])), 1)

    def test_09_search_jobs_keyword_search(self):
        """search_jobs: parametric keyword search returns jobs matching criteria."""
        res = s.search_jobs(query="Python", location="Bangalore", limit=5, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("objects", result)
        self.assertGreater(result.get("meta", {}).get("total_count", 0), 100)

    # =======================================================================
    # 4. GET_JOB_DETAILS MATRIX
    # =======================================================================

    def test_10_get_job_details_single_id(self):
        """get_job_details: inspecting a single job ID retrieves Schema.org metadata."""
        res = s.get_job_details(job_ids=447851, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        job = res.get("job", {})
        self.assertIn("Hoomanely", str(job))
        self.assertIn("description", job)

    def test_11_get_job_details_opportunity_url(self):
        """get_job_details: direct opportunity_url resolves full job description."""
        url = "/job-447851-sde-ii-full-stack-at-hoomanely-bangalore/"
        res = s.get_job_details(opportunity_url=url, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        job = res.get("job", {})
        self.assertEqual(job.get("company_name"), "Hoomanely")

    def test_12_get_job_details_batch(self):
        """get_job_details: inspecting multiple job IDs returns batch list."""
        res = s.get_job_details(job_ids=[447851, 470367], sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        self.assertEqual(res.get("count"), 2)

    # =======================================================================
    # 5. MANAGE_JOB_PIPELINE MATRIX
    # =======================================================================

    def test_13_manage_job_pipeline_metrics(self):
        """manage_job_pipeline: action='metrics' fetches live opportunity breakdown."""
        res = s.manage_job_pipeline(action="metrics", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("status_counts", result)
        self.assertIn("location_counts", result)

    def test_14_manage_job_pipeline_list_applied(self):
        """manage_job_pipeline: action='list_applied' returns applied opportunities."""
        res = s.manage_job_pipeline(action="list_applied", limit=5, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("objects", result)

    def test_15_manage_job_pipeline_list_declined(self):
        """manage_job_pipeline: action='list_declined' returns passed opportunities."""
        res = s.manage_job_pipeline(action="list_declined", limit=5, sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("objects", result)

    # =======================================================================
    # 6. MANAGE_ACCOUNT MATRIX
    # =======================================================================

    def test_16_manage_account_get_settings(self):
        """manage_account: action='get_settings' returns privacy and notification settings."""
        res = s.manage_account(action="get_settings", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        settings = res.get("settings", {})
        self.assertEqual(settings.get("name"), "Prasad Rawas")
        self.assertIn("companies_to_block", settings)

    def test_17_manage_account_suggest_locations(self):
        """manage_account: action='suggest' category='locations' returns location taxonomy."""
        res = s.manage_account(action="suggest", suggest_category="locations", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("cities_preferred", result.get("data", {}))

    def test_18_manage_account_suggest_functions(self):
        """manage_account: action='suggest' category='job_functions' returns role functions."""
        res = s.manage_account(action="suggest", suggest_category="job_functions", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertGreater(len(result.get("objects", [])), 50)

    def test_19_manage_account_suggest_employers(self):
        """manage_account: action='suggest' category='top_employers' returns top companies."""
        res = s.manage_account(action="suggest", suggest_category="top_employers", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertGreater(len(result.get("objects", [])), 10)

    def test_20_manage_account_get_messages(self):
        """manage_account: action='get_messages' fetches recruiter inbox conversations."""
        res = s.manage_account(action="get_messages", sessionid=self.sid, csrftoken=self.csrf, cf_clearance=self.cf, user_agent=self.ua)
        self.assertEqual(res.get("status_code"), 200)
        result = res.get("result", {})
        self.assertIn("objects", result)
        self.assertIn("unread_message_count", result)


if __name__ == "__main__":
    unittest.main()
