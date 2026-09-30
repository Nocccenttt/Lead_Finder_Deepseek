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
    """Extract only the explicit external site URL shown by an Admire entry."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
            self.visible_text = []
            self.capture = False

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            href = attrs.get("href", "")
            if href:
                self.links.append((href, attrs))
            classes = (attrs.get("class") or "").lower()
            if tag == "a" and (
                "visit" in classes
                or "website" in classes
                or "external" in classes
            ):
                self.capture = True

        def handle_endtag(self, tag):
            if tag == "a":
                self.capture = False

        def handle_data(self, data):
            if self.capture:
                self.visible_text.append(data.strip())

    parser = LinkParser()
    parser.feed(entry_html)

    # Prefer external links whose attributes identify the submitted website.
    for href, attrs in parser.links:
        classes = (attrs.get("class") or "").lower()
        title = (attrs.get("title") or "").lower()
        aria = (attrs.get("aria-label") or "").lower()
        if any(term in f"{classes} {title} {aria}" for term in ("visit", "website", "external")):
            candidate = _clean_reference_url(urljoin(REFERENCE_HUB_URL, href))
            if candidate:
                return candidate

    # Admire currently renders the submitted URL as visible page text.
    import re
    for match in re.findall(r'https?://[^\s<>"\']+', entry_html):
        candidate = _clean_reference_url(match)
        if candidate:
            return candidate

    return ""



def _test():
    tests = {
        "Ragged Edge": "https://admiretheweb.com/inspiration/ragged-edge/",
        "North Design": "https://admiretheweb.com/inspiration/north-design/",
        "Geist Studio": "https://admiretheweb.com/inspiration/geist-studio/",
        "Special Projects": "https://admiretheweb.com/inspiration/special-projects/",
    }

    for name, url in tests.items():
        try:
            html = fetch_reference_page(url, 24000)
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
