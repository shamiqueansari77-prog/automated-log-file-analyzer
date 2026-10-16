"""
test_suite.py - Automated Comprehensive Verification Script
Tests routes, upload validation, analysis accuracy, health logic, report generation, and security.
"""

import io
import os
import re
import unittest
from app import app
import analyzer


class AutomatedLogAnalyzerTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def test_01_homepage_renders(self):
        """Verify GET / returns HTTP 200 and renders brand title and upload form."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("AUTOMATED LOG FILE ANALYZER", html)
        self.assertIn("Upload. Analyze. Detect. Report.", html)
        self.assertIn("Select Log Source", html)
        self.assertIn("Analyze Log", html)

    def test_02_analyze_sample_log(self):
        """Verify POST /analyze with sample.log computes metrics and renders dashboard."""
        sample_path = os.path.join(self.base_dir, "sample.log")
        self.assertTrue(os.path.exists(sample_path), "sample.log must exist in project root")

        with open(sample_path, "rb") as f:
            data = {
                "log_file": (f, "sample.log")
            }
            response = self.client.post("/analyze", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Check stat values are rendered
        self.assertIn("TOTAL LOGS", html)
        self.assertIn("INFO", html)
        self.assertIn("WARNINGS", html)
        self.assertIn("ERRORS", html)
        self.assertIn("CRITICAL", html)
        self.assertIn("DEBUG", html)

        # Check health panel is rendered
        self.assertIn("SYSTEM HEALTH", html)
        self.assertIn("Critical", html)

        # Check repeated issues
        self.assertIn("REPEATED ISSUES", html)
        self.assertIn("Database connection failed", html)
        self.assertIn("occurrences", html)

        # Check important issues
        self.assertIn("IMPORTANT ISSUES", html)
        self.assertIn("Server process crashed", html)

        # Check report download button & report_id link
        self.assertIn("/download-report/", html)
        self.assertIn("EXPORT REPORT", html)

        # Extract report ID
        match = re.search(r"/download-report/([a-f0-9]+)", html)
        self.assertIsNotNone(match, "Report ID must be generated and linked in UI")
        report_id = match.group(1)

        # Test download of this report
        rep_resp = self.client.get(f"/download-report/{report_id}")
        self.assertEqual(rep_resp.status_code, 200)
        self.assertEqual(rep_resp.mimetype, "text/plain")
        rep_text = rep_resp.get_data(as_text=True)
        self.assertIn("AUTOMATED LOG FILE ANALYZER - ANALYSIS REPORT", rep_text)
        self.assertIn("File Name:          sample.log", rep_text)
        self.assertIn(f"Report ID:          {report_id}", rep_text)
        self.assertIn("Database connection failed", rep_text)

    def test_03_invalid_file_extension(self):
        """Verify uploading an unsupported extension is rejected with friendly flash message."""
        data = {
            "log_file": (io.BytesIO(b"malicious script content"), "test_script.py")
        }
        response = self.client.post("/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Unsupported file format", html)

    def test_04_empty_file_upload(self):
        """Verify uploading an empty file is handled gracefully."""
        data = {
            "log_file": (io.BytesIO(b"   \n  \n"), "empty.log")
        }
        response = self.client.post("/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("The uploaded file is empty", html)

    def test_05_no_file_selected(self):
        """Verify submitting form without choosing a file is handled gracefully."""
        data = {
            "log_file": (io.BytesIO(b""), "")
        }
        response = self.client.post("/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No file was selected", html)

    def test_06_report_id_security_and_validation(self):
        """Verify invalid report format is rejected and flashes error."""
        response = self.client.get("/download-report/invalid-id-with-special!@#", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Invalid report identifier specified", html)

        # Test non-existent valid hex format
        non_existent = self.client.get("/download-report/deadbeefcafebabe", follow_redirects=True)
        self.assertEqual(non_existent.status_code, 200)
        html2 = non_existent.get_data(as_text=True)
        self.assertIn("Requested report was not found or has expired", html2)

    def test_07_analyzer_health_calculation_rules(self):
        """Verify deterministic rule-based health calculation matches specifications."""
        # 1. Critical > 0 -> Critical
        h1 = analyzer.calculate_health(1, 0, 0, 10)
        self.assertEqual(h1["status"], "Critical")

        # 2. Error >= 10 -> High Risk
        h2 = analyzer.calculate_health(0, 12, 0, 50)
        self.assertEqual(h2["status"], "High Risk")

        # 3. Error >= 20% -> High Risk
        h3 = analyzer.calculate_health(0, 3, 0, 10)
        self.assertEqual(h3["status"], "High Risk")

        # 4. Error > 0 -> Needs Attention
        h4 = analyzer.calculate_health(0, 1, 2, 20)
        self.assertEqual(h4["status"], "Needs Attention")

        # 5. Warning > 0 -> Warning
        h5 = analyzer.calculate_health(0, 0, 3, 20)
        self.assertEqual(h5["status"], "Warning")

        # 6. Healthy -> Healthy
        h6 = analyzer.calculate_health(0, 0, 0, 20)
        self.assertEqual(h6["status"], "Healthy")


if __name__ == "__main__":
    unittest.main()
