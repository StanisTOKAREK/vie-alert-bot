from pathlib import Path

from vie_alert_bot import extract_offers


def test_extract_offers():
    fixture_path = Path(__file__).parent / "fixtures" / "sample.html"
    html = fixture_path.read_text(encoding="utf-8")
    offers = extract_offers(html, base_url="https://mon-vie-via.businessfrance.fr")
    urls = {offer["url"] for offer in offers}

    assert "https://mon-vie-via.businessfrance.fr/offres/12345" in urls
    assert "https://mon-vie-via.businessfrance.fr/offres/67890" in urls
    assert len(offers) == 2
