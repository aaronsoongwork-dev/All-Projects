from emailclf.cleaning import build_text, clean_body, normalize_subject, remove_quoted_reply, remove_signature, strip_html


def test_strip_html_keeps_text_and_drops_tags_and_styles():
    html = "<html><head><style>p{color:red}</style></head><body><p>Hello <b>Aisyah</b></p><p>Next line</p></body></html>"
    out = strip_html(html)
    assert "Hello Aisyah" in out and "Next line" in out
    assert "color:red" not in out and "<" not in out


def test_quoted_reply_chain_is_removed():
    text = "We will not proceed.\n\nOn Mon, 18 Nov 2025 at 09:12, Aisyah <a@b.com> wrote:\n> Thank you for applying"
    out = remove_quoted_reply(text)
    assert out == "We will not proceed."


def test_outlook_header_block_is_removed():
    text = "Sounds good.\n\nFrom: Marcus\nSent: Monday\nTo: Aisyah\nSubject: Hi\n\nOld text"
    assert remove_quoted_reply(text) == "Sounds good."


def test_inline_quote_lines_removed():
    assert remove_quoted_reply("Answer here\n> old line\nmore answer") == "Answer here\nmore answer"


def test_if_everything_is_quoted_we_keep_original():
    text = "> only quoted text"
    assert remove_quoted_reply(text) == text


def test_signature_after_closing_is_removed():
    text = "Please submit your CV.\n\nBest regards,\nFarah Rahman\nPeople & Culture\nBrightwave Systems\n+60 3-1234 5678"
    assert remove_signature(text) == "Please submit your CV."


def test_thank_you_followed_by_a_real_sentence_is_NOT_cut():
    text = "Thank you\nPlease complete the assessment by Friday."
    assert "complete the assessment" in remove_signature(text)


def test_dash_dash_delimiter_and_disclaimer_and_mobile_signature():
    assert remove_signature("Body\n-- \nJohn\nCEO") == "Body"
    assert remove_signature("Body\n\nCONFIDENTIALITY NOTICE: secret stuff") == "Body"
    assert remove_signature("Body\n\nSent from my iPhone") == "Body"


def test_urls_are_replaced():
    assert "<URL>" in clean_body("Click https://evil.example/a?b=1 now")


def test_subject_prefix_removed():
    assert normalize_subject("Re: Fwd: RE: Hello") == "Hello"


def test_full_messy_email_reduces_to_the_message():
    raw = ('<html><body><p>Unfortunately we will not be moving forward.</p><p>Regards,<br>Marcus<br>Nordlane</p>'
           '<p>On Mon, 3 Mar 2025 at 10:00, Aisyah wrote:</p><blockquote>&gt; Thank you for applying</blockquote></body></html>')
    out = clean_body(raw)
    assert "not be moving forward" in out
    assert "Thank you for applying" not in out
    assert "Marcus" not in out


def test_build_text_without_cleaning_keeps_raw():
    assert "<p>" in build_text("S", "<p>x</p>", clean=False)
