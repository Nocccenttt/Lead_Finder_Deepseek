def _clean_reference_url(url: str) -> str:
    """Return a real external reference URL or an empty string."""
    from urllib.parse import urlparse

    url = (url or "").strip().strip("()[]<>\"'")
    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().split(":")[0]
    blocked = (
        "admiretheweb.com",
        "schema.org",
        "googleapis.com",
        "gstatic.com",
        "feedburner.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "youtu.be",
        "pinterest.com",
        "tiktok.com",
    )
    if not host or any(host == item or host.endswith("." + item) for item in blocked):
        return ""

    path = parsed.path.lower()
    if any(part in path for part in ("/wp-content/", "/wp-includes/", "/assets/", "/static/")):
        return ""

    return url.rstrip("/")




def _extract_submitted_site(entry_html: str) -> str:
    """Extract the external site from Admire's known c-item markup."""
    import re
    from html import unescape

    # The captured Admire page puts the submitted URL directly in the
    # c-item image link and repeats it as the c-item title link.
    patterns = (
        r'class=["\'][^"\']*\bc-item__image\b[^"\']*["\'][\s\S]{0,2500}?'
        r'<a\b[^>]*\bhref=["\'](https?://[^"\']+)["\']',
        r'class=["\'][^"\']*\bc-item__title\b[^"\']*["\'][\s\S]{0,500}?'
        r'<a\b[^>]*\bhref=["\'](https?://[^"\']+)["\']',
    )

    for pattern in patterns:
        match = re.search(pattern, entry_html, flags=re.I)
        if match:
            candidate = _clean_reference_url(unescape(match.group(1)))
            if candidate:
                return candidate

    return ""

def fetch_reference_page(url: str, max_chars: int = 200000) -> str:
    from urllib.request import Request, urlopen
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LeadFinder/1.0)"},
    )
    with urlopen(request, timeout=15) as response:
        raw = response.read(max_chars)
    return raw.decode("utf-8", errors="ignore")


def _test():
    tests = {
        "Ragged Edge": "https://admiretheweb.com/inspiration/ragged-edge/",
        "North Design": "https://admiretheweb.com/inspiration/north-design/",
        "Geist Studio": "https://admiretheweb.com/inspiration/geist-studio/",
        "Special Projects": "https://admiretheweb.com/inspiration/special-projects/",
    }

    for name, url in tests.items():
        try:
            html = fetch_reference_page(url, 200000)
            result = _extract_submitted_site(html)
            print(f"{name}: {result or 'FAIL'}")
            assert result, f"{name}: no submitted website found"
            assert "cdn.usefathom.com" not in result
            assert "schema.org" not in result
            assert "admiretheweb.com" not in result
        except Exception as exc:
            print(f"{name}: ERROR {exc}")
            raise

    print("REFERENCE EXTRACTOR TEST: PASS")


if __name__ == "__main__":
    _test()
