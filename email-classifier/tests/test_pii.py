from emailclf.pii import redact


def test_email_and_phone_are_masked():
    text, counts = redact("Contact aisyah@example.com or +60 3-1234 5678 today")
    assert "aisyah@example.com" not in text and "[EMAIL]" in text
    assert "[PHONE]" in text
    assert counts["EMAIL"] == 1 and counts["PHONE"] == 1


def test_dates_and_small_numbers_are_not_phone_numbers():
    text, counts = redact("Deadline 2025-12-15, salary RM 9,000, 90 minutes")
    assert "[PHONE]" not in text and counts == {}


def test_card_and_id_masked():
    text, counts = redact("Card 4111 1111 1111 1111 and ID 900101-14-5678")
    assert "4111" not in text and "900101" not in text
