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
    """Extract a submitted website from visible Admire anchor elements only."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
            self.current = None

        def handle_starttag(self, tag, attrs):
            if tag != "a":
                return
            attrs = dict(attrs)
            self.current = {
                "href": attrs.get("href", ""),
                "class": attrs.get("class", ""),
                "title": attrs.get("title", ""),
                "aria": attrs.get("aria-label", ""),
                "text": [],
            }

        def handle_data(self, data):
            if self.current is not None:
                self.current["text"].append(data)

        def handle_endtag(self, tag):
            if tag == "a" and self.current is not None:
                self.current["text"] = " ".join(self.current["text"]).strip()
                self.links.append(self.current)
                self.current = None

    parser = LinkParser()
    parser.feed(entry_html)

    # 1. Prefer an anchor explicitly labeled as the submitted website.
    for link in parser.links:
        label = " ".join(
            [link["text"], link["class"], link["title"], link["aria"]]
        ).lower()
        if any(term in label for term in (
            "visit website",
            "visit site",
            "view website",
            "website",
        )):
            candidate = _clean_reference_url(
                urljoin(REFERENCE_HUB_URL, link["href"])
            )
            if candidate:
                return candidate

    # 2. Prefer visible anchor text that is itself a URL.
    for link in parser.links:
        text = link["text"].strip()
        if text.lower().startswith(("http://", "https://", "www.")):
            candidate = _clean_reference_url(text)
            if candidate:
                return candidate

    # 3. Never inspect raw HTML URLs. That is what caused the Fathom false positive.
    return ""

def fetch_reference_page(url: str, max_chars: int = 24000) -> str:
    from urllib.request import Request, urlopen
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LeadFinder/1.0)"},
    )
    with urlopen(request, timeout=15) as response:
        raw = response.read(max_chars * 4)
    return raw.decode("utf-8", errors="ignore")[:max_chars]


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
