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
    """Extract the submitted site from Admire's c-item link."""
    from html.parser import HTMLParser

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_item = False
            self.item_depth = 0
            self.links = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            classes = (attrs.get("class") or "").split()

            if tag in ("article", "div", "figure") and "c-item" in classes:
                self.in_item = True
                self.item_depth = 1
                return

            if self.in_item:
                if tag in ("article", "div", "figure"):
                    self.item_depth += 1

                if tag == "a":
                    self.links.append({
                        "href": attrs.get("href", ""),
                        "target": attrs.get("target", ""),
                        "text": [],
                    })

        def handle_data(self, data):
            if self.links and self.in_item:
                self.links[-1]["text"].append(data)

        def handle_endtag(self, tag):
            if self.in_item and tag in ("article", "div", "figure"):
                self.item_depth -= 1
                if self.item_depth <= 0:
                    self.in_item = False
                    self.item_depth = 0

    parser = LinkParser()
    parser.feed(entry_html)

    # Admire's actual structure has the submitted site in:
    # <article class="c-item c-item--full">
    #   <a href="https://example.com/" target="_blank">
    # and again as visible URL text.
    for link in parser.links:
        href = link["href"].strip()
        visible = " ".join(link["text"]).strip()

        candidate = _clean_reference_url(href)
        if not candidate:
            candidate = _clean_reference_url(visible)

        if candidate:
            return candidate

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
