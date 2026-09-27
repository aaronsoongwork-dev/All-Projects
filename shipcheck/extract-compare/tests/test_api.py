import sys
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from api.db import get_session
from api.main import app
from core.classifier import ClassificationResult
from core.compare_ai import ComparisonResult, FieldComparison


class TestFastAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(cls.test_engine)

        def override_get_session():
            with Session(cls.test_engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("docs", data)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("providers", data)

    def test_classify_endpoint_mock(self):
        with patch("api.routes.classify._classifier.classify") as mock_classify:
            mock_classify.return_value = ClassificationResult(
                category="BL_COMPARISON",
                confidence=0.98,
                probabilities={"BL_COMPARISON": 0.98, "GENERAL": 0.02},
            )

            payload = {
                "subject": "Attached SI and draft BL for checking",
                "snippet": "Please compare OC 5ALT-01226",
                "body": "Hi, please check attached SI vs draft BL.",
            }

            response = self.client.post("/api/classify", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["type"], "Document Comparison")
            self.assertEqual(data["confidence"], 0.98)
            self.assertIsNotNone(data["reasoning"])

    def test_classify_endpoint_fallback(self):
        # When classifier raises ValueError (e.g. no API key configured)
        with patch("api.routes.classify._classifier.classify", side_effect=ValueError("API key missing")):
            payload = {
                "subject": "Invoice dispute regarding demurrage",
                "snippet": "Incorrect amount billed",
                "body": "Please revise the invoice immediately.",
            }
            response = self.client.post("/api/classify", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["type"], "Invoice Query")
            self.assertIn("Heuristic fallback", data["reasoning"])

    def test_compare_text_endpoint(self):
        mock_si = {
            "shipper": "Alpha Corp",
            "consignee": "Beta LLC",
            "notify_party": "Gamma Inc",
            "port_of_loading": "SINGAPORE",
            "port_of_discharge": "ROTTERDAM",
            "container_count": "2 x 40'HC",
            "gross_weight_kg": 25000,
        }
        mock_bl = dict(mock_si)
        mock_bl["gross_weight_kg"] = 26000  # mismatch

        with patch("api.routes.compare.extract_fields", side_effect=[mock_si, mock_bl]):
            payload = {
                "si_text": "Sample SI text",
                "bl_text": "Sample BL text",
            }
            response = self.client.post("/api/compare/text", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "Mismatch")
            self.assertEqual(len(data["fields"]), 7)

            # verify Gross Weight field
            gw_field = next(f for f in data["fields"] if "Gross Weight" in f["field"])
            self.assertFalse(gw_field["match"])
            self.assertEqual(gw_field["si"], "25000")
            self.assertEqual(gw_field["bl"], "26000")

    def test_compare_files_endpoint(self):
        mock_si = {
            "shipper": "Alpha Corp",
            "consignee": "Beta LLC",
            "notify_party": "Gamma Inc",
            "port_of_loading": "SINGAPORE",
            "port_of_discharge": "ROTTERDAM",
            "container_count": "2 x 40'HC",
            "gross_weight_kg": 25000,
        }
        mock_bl = dict(mock_si)

        with patch("api.routes.compare._extractor.extract_from_bytes", side_effect=[(mock_si, "text"), (mock_bl, "text")]):
            files = {
                "si_file": ("si.txt", b"SI content", "text/plain"),
                "bl_file": ("bl.txt", b"BL content", "text/plain"),
            }
            response = self.client.post("/api/compare", files=files)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "Match")
            self.assertTrue(all(f["match"] for f in data["fields"]))

    def test_compare_email_attachments_endpoint(self):
        """Verifies /api/compare/email auto-identifies SI/BL among attachments and compares them."""
        mock_si = {
            "shipper": "Alpha Corp",
            "consignee": "Beta LLC",
            "notify_party": "Gamma Inc",
            "port_of_loading": "SINGAPORE",
            "port_of_discharge": "ROTTERDAM",
            "container_count": "2 x 40'HC",
            "gross_weight_kg": 25000,
        }
        mock_bl = dict(mock_si)
        mock_bl["gross_weight_kg"] = 26000  # mismatch

        # SI/BL attachments now extract concurrently (see core/check_email.py
        # identify_si_bl), so the mock must key off filename rather than call
        # order - a positional side_effect list would race between threads.
        def fake_extract(filename, raw_bytes):
            return (mock_si, "text") if "si" in filename else (mock_bl, "text")

        with patch("api.comparison_service.extractor.extract_from_bytes", side_effect=fake_extract):
            files = [
                ("attachments", ("doc_si.txt", b"SHIPPING INSTRUCTION\nfoo", "text/plain")),
                ("attachments", ("doc_bl.txt", b"BILL OF LADING\nfoo", "text/plain")),
            ]
            response = self.client.post(
                "/api/compare/email",
                data={"email_id": "msg_auto_1"},
                files=files,
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "Mismatch")
            self.assertIsNotNone(data["comparison_id"])

    def test_compare_email_attachments_needs_review_when_undersupplied(self):
        """Fewer than 2 attachments should fall back to Needs Review, not error."""
        files = [("attachments", ("doc_si.txt", b"SHIPPING INSTRUCTION\nfoo", "text/plain"))]
        response = self.client.post(
            "/api/compare/email",
            data={"email_id": "msg_auto_2"},
            files=files,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "Needs Review")

    def test_sync_user_identities_synchronization(self):
        """Verifies /api/auth/sync-user creates auth.users and auth.identities with correct parameters."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None  # user doesn't exist yet

        executed_sqls = []
        executed_params = []

        def track_execute(stmt, params=None):
            executed_sqls.append(str(stmt))
            if params:
                executed_params.append(params)
            mock_res = MagicMock()
            mock_res.fetchone.return_value = None
            return mock_res

        mock_conn.execute.side_effect = track_execute

        with patch("api.routes.auth.engine.connect") as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn

            payload = {
                "email": "testuser@gmail.com",
                "name": "Test User",
                "picture": "https://example.com/avatar.png",
                "provider": "google",
            }
            response = self.client.post("/api/auth/sync-user", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["email"], "testuser@gmail.com")
            self.assertEqual(data["name"], "Test User")
            self.assertTrue(len(data["token"]) > 10)

            # Check that auth.identities SQL was executed
            identity_sqls = [s for s in executed_sqls if "INSERT INTO auth.identities" in s]
            self.assertEqual(len(identity_sqls), 1)
            ident_sql = identity_sqls[0]

            # Verify the generated column 'email' is omitted from INSERT INTO auth.identities
            # It should have: id, provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at
            columns_part = ident_sql.split("(")[1].split(")")[0]
            col_names = [c.strip() for c in columns_part.split(",")]
            self.assertNotIn("email", col_names)
            self.assertIn("provider_id", col_names)
            self.assertIn("identity_data", col_names)
            self.assertIn("provider", col_names)

            # Check parameters
            ident_param = next(p for p in executed_params if "pid" in p)
            self.assertEqual(ident_param["provider"], "google")
            ident_data = json.loads(ident_param["data"])
            self.assertEqual(ident_data["email"], "testuser@gmail.com")
            self.assertEqual(ident_data["full_name"], "Test User")
            self.assertEqual(ident_data["sub"], data["user_id"])


if __name__ == "__main__":
    unittest.main()

