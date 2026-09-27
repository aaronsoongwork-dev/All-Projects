import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.classifier import EmailClassifier, ClassificationResult
from core.compare_ai import (
    ValueNormalizer,
    FieldComparison,
    ComparisonResult,
    DocumentComparator,
    normalize,
    compare_fields_hybrid,
)
from core.check_email import (
    EmailMessage,
    AttachmentExtractor,
    EmailVerificationPipeline,
    VerificationReport,
    ConsoleReporter,
)


class TestEmailClassifier(unittest.TestCase):
    def test_classification_result_properties(self):
        res = ClassificationResult(
            category="BL_COMPARISON",
            confidence=0.95,
            probabilities={"BL_COMPARISON": 0.95, "GENERAL": 0.05},
        )
        self.assertTrue(res.is_bl_comparison)
        summary = res.summary()
        self.assertIn("BL_COMPARISON", summary)
        self.assertIn("0.9500", summary)

        res2 = ClassificationResult(category="SPAM")
        self.assertFalse(res2.is_bl_comparison)

    def test_classifier_mock(self):
        classifier = EmailClassifier()
        mock_response = MagicMock()
        mock_answer = MagicMock()
        mock_answer.choice = "BL_COMPARISON"
        mock_answer.confidence = 0.98
        mock_answer.probabilities = {"BL_COMPARISON": 0.98}
        mock_response.answers = {"category": mock_answer}

        classifier.classify_email = MagicMock(return_value=mock_response)

        email = EmailMessage(
            email_id="email_001",
            sender="ops@shipping.com",
            subject="Check SI vs BL",
            body="Please compare attached",
            attachments=["email_001_SI.pdf", "email_001_BL.pdf"],
        )
        result = classifier.classify(email)
        self.assertEqual(result.category, "BL_COMPARISON")
        self.assertEqual(result.confidence, 0.98)
        self.assertTrue(result.is_bl_comparison)


class TestCompareAI(unittest.TestCase):
    def test_value_normalizer(self):
        normalizer = ValueNormalizer()
        self.assertIsNone(normalizer.normalize(None))
        self.assertEqual(normalizer.normalize(""), "")
        self.assertEqual(normalizer.normalize("  ABC  DEF  "), "ABC DEF")
        self.assertEqual(normalizer.normalize("line1\nline2|line3;line4"), "LINE1 LINE2 LINE3 LINE4")
        self.assertEqual(normalize("Co., Ltd."), "CO. LTD.")

    def test_comparator_deterministic_match(self):
        comparator = DocumentComparator()
        si = {
            "shipper": "Alpha Corp\n123 Street",
            "consignee": "Beta LLC",
            "gross_weight_kg": 15000,
        }
        bl = {
            "shipper": "ALPHA CORP | 123 STREET",
            "consignee": "Beta LLC",
            "gross_weight_kg": 15000,
        }
        res = comparator.compare(si, bl, ["shipper", "consignee", "gross_weight_kg"])
        self.assertTrue(res.is_match)
        self.assertFalse(res.has_defect)
        self.assertEqual(res.defect_fields, [])
        self.assertTrue(res.field_comparisons["shipper"].is_match)
        self.assertFalse(res.field_comparisons["shipper"].ai_evaluated)

    def test_comparator_numeric_mismatch(self):
        comparator = DocumentComparator()
        si = {"gross_weight_kg": 15000}
        bl = {"gross_weight_kg": 20000}
        res = comparator.compare(si, bl, ["gross_weight_kg"])
        self.assertFalse(res.is_match)
        self.assertIn("gross_weight_kg", res.defect_fields)

    def test_comparator_ai_pass(self):
        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "tool_use"
        mock_block.name = "compare_field_values"
        mock_block.input = {
            "comparisons": [
                {"field": "shipper", "same": True, "reasoning": "Same company despite different formatting."}
            ]
        }
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response

        comparator = DocumentComparator(client=mock_client)
        si = {"shipper": "Acme Inc, Road 5"}
        bl = {"shipper": "Acme Inc - PO Box 999"}  # Normalization will differ

        res = comparator.compare(si, bl, ["shipper"])
        self.assertTrue(res.is_match)
        self.assertTrue(res.field_comparisons["shipper"].ai_evaluated)
        self.assertEqual(res.ai_reasoning["shipper"], "Same company despite different formatting.")

    def test_compare_fields_hybrid_wrapper(self):
        si = {"gross_weight_kg": 1000}
        bl = {"gross_weight_kg": 2000}
        defects, reasoning = compare_fields_hybrid(si, bl, ["gross_weight_kg"])
        self.assertEqual(defects, ["gross_weight_kg"])
        self.assertEqual(reasoning, {})


class TestCheckEmailPipeline(unittest.TestCase):
    def test_email_message(self):
        msg = EmailMessage.from_dict({
            "email_id": "email_010",
            "from": "user@domain.com",
            "subject": "SI vs BL",
            "body": "Here are docs",
            "attachments": ["subfolder/email_010_SI.pdf", "subfolder/email_010_BL.pdf"],
        })
        self.assertEqual(msg.email_id, "email_010")
        self.assertEqual(msg.find_si_attachment(), "subfolder/email_010_SI.pdf")
        self.assertEqual(msg.find_bl_attachment(), "subfolder/email_010_BL.pdf")

    def test_pipeline_non_comparison(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(category="GENERAL")

        pipeline = EmailVerificationPipeline(classifier=mock_classifier)
        email = EmailMessage.from_dict({
            "email_id": "email_002",
            "from": "user@test.com",
            "subject": "General question",
            "body": "Hi there",
            "attachments": [],
        })

        report = pipeline.verify(email)
        self.assertEqual(report.status, "NOT_COMPARISON")

    def test_pipeline_missing_attachment(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(category="BL_COMPARISON")

        pipeline = EmailVerificationPipeline(classifier=mock_classifier)
        email = EmailMessage.from_dict({
            "email_id": "email_003",
            "from": "user@test.com",
            "subject": "Compare docs",
            "body": "Only SI attached",
            "attachments": ["email_003_SI.pdf"],
        })

        report = pipeline.verify(email)
        self.assertEqual(report.status, "NEEDS_REVIEW")
        self.assertEqual(report.review_reason, "missing_attachment")

    def test_pipeline_full_run(self):
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = ClassificationResult(category="BL_COMPARISON")

        mock_extractor = MagicMock()
        mock_extractor.extract_from_file.side_effect = [
            ({"shipper": "Acme", "gross_weight_kg": 100}, "text"),
            ({"shipper": "Acme", "gross_weight_kg": 100}, "text"),
        ]

        mock_comparator = DocumentComparator()
        pipeline = EmailVerificationPipeline(
            classifier=mock_classifier,
            extractor=mock_extractor,
            comparator=mock_comparator,
            fields=["shipper", "gross_weight_kg"],
        )

        email = EmailMessage.from_dict({
            "email_id": "email_004",
            "from": "user@test.com",
            "subject": "Compare docs",
            "body": "Both attached",
            "attachments": ["email_004_SI.pdf", "email_004_BL.pdf"],
        })

        report = pipeline.verify(email)
        self.assertEqual(report.status, "OK")
        self.assertEqual(report.si_method, "text")
        self.assertTrue(report.comparison.is_match)


if __name__ == "__main__":
    unittest.main()

