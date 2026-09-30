import argparse
import json
import os
import re
from html import escape, unescape
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from openai import OpenAI

from api_usage_logger import log_usage


load_dotenv()

MODEL = "deepseek-chat"


REFERENCE_HUB_URL = os.getenv(
    "DESIGN_REFERENCE_HUB_URL",
    "https://admiretheweb.com/",
)

REFERENCE_LIMIT = 4

REFERENCE_HUB_RULES = """
Use Admire The Web only as a REFERENCE HUB. It is not the design reference.

The workflow is:
1. Discover individual website entries from the hub.
2. Inspect the actual external website behind the selected entry.
3. Select ONE actual website as the primary design reference.
4. Analyze that actual website's design language.
5. Create an ORIGINAL design for the supplied business using selected principles only.

Never use the Admire The Web homepage, category page, or gallery itself as the visual reference.
Never copy the selected website's branding, copy, assets, exact layout, or distinctive composition.
The selected website is a design-language reference only.
"""



SYSTEM_PROMPT = """
You are a senior local SEO strategist, conversion copywriter, and Design Director creating an original,
high-converting website preview for a local business.

The supplied source data contains verified business information. Use verified facts for company claims.
The business niche may be inferred from an explicit niche/category or an obvious business name.

NEVER invent company-specific facts such as reviews, ratings, testimonials, awards, certifications,
licenses, years in business, customer counts, guarantees, pricing, discounts, statistics, staff,
locations, service areas, business hours, insurance status, or unsupported credentials.

You MAY create useful general educational/contextual content about the business category and local search
intent. General industry information must NOT be presented as a fact about the business.

The final website will be rebuilt ONLY in WordPress using Elementor / Elementor Pro.
Every design decision must be realistically achievable with Elementor containers, widgets, responsive
controls, global colors/fonts, custom CSS, and minimal front-end JavaScript.

REFERENCE RULES:
- Admire The Web is a HUB OF OPTIONS, not the design reference.
- Select exactly ONE individual website from the supplied reference candidates.
- The candidates include compact research from the actual external websites.
- Analyze the ACTUAL selected website, not Admire The Web itself.
- Use the selected site's design language as inspiration only.
- Do not copy its branding, copy, assets, exact layout, or distinctive composition.
- Adapt the useful principles to the business niche, local audience, SEO intent, conversion goal,
  verified content, and Elementor constraints.
- Prefer a coherent set of 3-6 traits from the selected site over a mixture of unrelated references.
- reference_influences must describe what was borrowed as a general design principle, not copied elements.

Return ONLY valid JSON with exactly this structure. Keep every text field concise:
{
  "seo": {
    "title": "",
    "meta_description": "",
    "primary_keyword": "",
    "secondary_keywords": [],
    "search_intent": ""
  },
  "design_spec": {
    "direction": "",
    "visual_style": "",
    "layout_style": "",
    "hero_style": "",
    "navigation_style": "",
    "color_direction": {
      "primary": "",
      "accent": "",
      "background": "",
      "text": ""
    },
    "design_system": {
      "palette": {
        "background": "",
        "surface": "",
        "surface_alt": "",
        "text": "",
        "muted": "",
        "primary": "",
        "accent": "",
        "dark": "",
        "on_primary": ""
      },
      "spacing": "",
      "container": "",
      "section_tone": "",
      "dark_sections": [],
      "motion": "",
      "radius": "",
      "shadow": ""
    },
    "reference_selection": {
      "name": "",
      "hub_url": "",
      "website_url": "",
      "reason": ""
    },
    "reference_analysis": {
      "navigation": "",
      "hero": "",
      "layout": "",
      "typography": "",
      "color": "",
      "spacing": "",
      "components": "",
      "motion": "",
      "responsive": ""
    },
    "reference_patterns": [],
    "reference_influences": [],
    "composition": {
      "about": "",
      "services": "",
      "benefits": "",
      "process": "",
      "local": "",
      "faq": "",
      "cta": ""
    },
    "typography_style": "",
    "card_style": "",
    "button_style": "",
    "section_order": [],
    "image_strategy": "",
    "elementor_compatible": true,
    "elementor_notes": []
  },
  "headline": "",
  "subheadline": "",
  "intro": "",
  "about_title": "",
  "about": "",
  "services_intro": "",
  "services": [],
  "benefits": [],
  "process": [
    {"title": "", "text": ""},
    {"title": "", "text": ""},
    {"title": "", "text": ""}
  ],
  "local_intro": "",
  "faq": [
    {"question": "", "answer": ""}
  ],
  "cta_title": "",
  "cta_text": "",
  "image_queries": [],
  "image_alt": []
}

SEO CONTENT RULES:
- Create content useful for a real SEO landing page, even though this is a preview.
- Identify one primary local search intent from the verified business niche and location.
- Use the business name and verified location naturally.
- Use relevant secondary keywords naturally; never keyword stuff.
- Do not claim that the business provides a service unless the source verifies it.
- If services are not verified, return an empty services array and use general/contextual wording elsewhere.
- Never invent service areas, credentials, experience, reviews, ratings, certifications, licenses, guarantees,
  pricing, or business history.

DESIGN RULES:
- Do not automatically use the same dark/gold design for every business.
- Derive the design system from the selected actual reference, then adapt it to this business.
- Keep one coherent palette; do not assign unrelated colors independently to sections.
- Use the selected reference's composition principles, not its exact layout.
- Avoid repetitive card grids, excessive rounded cards, generic gradients, and predictable template sections.
- section_order should contain only sections actually needed.
- composition must choose deliberate layouts such as split-media, editorial, asymmetric, feature-grid,
  steps, split-dark, accordion, contained-cta, stacked, minimal, or grid.
- Let content determine section height. Do not create large empty gaps just to imitate whitespace.
- Use useful contextual copy to create appropriate content density when verified business data is sparse.
- motion must be subtle CSS/IntersectionObserver behavior only.
- dark_sections should normally contain no more than 2 sections.
- design_system.palette must use valid 6-digit hex colors with strong contrast.
- spacing must be compact, comfortable, or spacious; container must be focused or wide.
- reference_patterns should contain 3-5 traits actually observed in the selected website.
- reference_influences should contain 2-4 concise mappings such as "Reference navigation -> sticky minimal header".
- reference_selection.website_url MUST exactly match one of the supplied candidate website_url values.
- reference_selection.hub_url must identify the Admire The Web entry where the website was discovered.
- reference_analysis must describe the selected actual website, not the hub.

CONTENT RULES:
- Write for the verified niche, not a hardcoded industry.
- Keep copy natural, useful, local, and conversion-focused.
- Benefits should describe general customer-facing value unless a company-specific benefit is verified.
- Process should remain general: Contact, Schedule/Plan, Service/Completion.
- FAQ answers must remain supported by the source or clearly general educational information.
- Do not use unsupported superlatives such as best, #1, top-rated, cheapest, fastest, most trusted, or guaranteed.
- Do not mention AI, LeadFinder, Wolf Forge, prompts, or internal processes.

IMAGES:
- The generated site MUST use relevant realistic photography related to the business niche.
- Return exactly 2 short image search queries.
- Do not request logos, fake company branding, screenshots, or identifiable celebrities.
- image_alt must contain 2 concise descriptive alt texts matching the image queries.
"""



def load_json(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def get_business_name(business, handoff):
    return (
        business.get("business_name")
        or business.get("name")
        or handoff.get("business_name")
        or handoff.get("business", {}).get("business_name")
        or handoff.get("business", {}).get("name")
        or "Local Business"
    )


def get_niche(business, handoff):
    return (
        business.get("niche")
        or business.get("category")
        or handoff.get("niche")
        or handoff.get("category")
        or business.get("business_name")
        or business.get("name")
        or "local business"
    )


def write_image_fallback(path, label):
    """Create a tiny local SVG fallback so the layout never has a broken image."""
    label = escape(str(label or "Local Business"))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000">
<rect width="1600" height="1000" fill="#0d1b2e"/>
<circle cx="1280" cy="250" r="280" fill="#13243a"/>
<circle cx="1280" cy="250" r="180" fill="#1b314d"/>
<text x="120" y="470" fill="#d7b56d" font-family="Arial,Helvetica,sans-serif"
      font-size="34" font-weight="700" letter-spacing="5">{label.upper()}</text>
<text x="120" y="530" fill="#f7f9fc" font-family="Arial,Helvetica,sans-serif"
      font-size="58" font-weight="700">Professional Local Service</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")
    return path.name


def download_stock_image(query, output_dir, filename):
    """
    Search Pexels and download one niche-matched photo locally.

    The finished website references the downloaded local file only.
    Falls back to a local SVG if the API key, search, or download fails.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import requests

        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise RuntimeError("PEXELS_API_KEY is not configured")

        query = str(query or "").strip() or "professional local business"

        search = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
            },
            timeout=20,
        )
        search.raise_for_status()

        data = search.json()
        photos = data.get("photos") or []
        if not photos:
            raise RuntimeError("Pexels returned no matching photos")

        photo = photos[0]
        image_url = (
            photo.get("src", {}).get("large2x")
            or photo.get("src", {}).get("large")
            or photo.get("src", {}).get("original")
        )
        if not image_url:
            raise RuntimeError("Pexels result did not contain a usable image URL")

        image = requests.get(
            image_url,
            timeout=30,
            headers={"User-Agent": "LeadFinder/1.0"},
            allow_redirects=True,
        )
        image.raise_for_status()

        content = image.content
        content_type = image.headers.get("Content-Type", "").lower()
        if not content or len(content) < 10_000:
            raise RuntimeError("Downloaded image was empty or unexpectedly small")

        extension = ".jpg"
        if "png" in content_type:
            extension = ".png"
        elif "webp" in content_type:
            extension = ".webp"

        target = output_dir / f"{filename}{extension}"
        target.write_bytes(content)

        photographer = photo.get("photographer") or "Pexels"
        print(f"[image] Pexels: {query} -> {photographer}")
        print(f"[image] Saved: {target}")
        return target.name

    except Exception as error:
        fallback = output_dir / f"{filename}.svg"
        write_image_fallback(fallback, query)
        print(f"[image] Pexels failed for '{query}': {error}")
        print(f"[image] Using local fallback: {fallback}")
        return fallback.name



def phone_link(phone):
    if not phone:
        return ""

    digits = "".join(
        c for c in str(phone)
        if c.isdigit() or c == "+"
    )

    return (
        f'<a class="button primary" href="tel:{escape(digits)}">'
        f"Call Now"
        f"</a>"
    )


def fetch_reference_page(url, max_chars=24000):
    """Fetch a public reference page using stdlib only."""
    request = Request(
        url,
        headers={
            "User-Agent": "LeadFinder Design Research/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    with urlopen(request, timeout=8) as response:
        raw = response.read(max_chars)
        charset = response.headers.get_content_charset() or "utf-8"

    return raw.decode(charset, errors="ignore")


def clean_reference_text(html, max_chars=1400):
    """Reduce HTML to a compact text snapshot for design research."""
    html = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    text_value = re.sub(r"\s+", " ", html).strip()
    return text_value[:max_chars]


def extract_reference_links(html, base_url):
    """Return unique absolute links from a page."""
    links = []
    for href in re.findall(r'''href\s*=\s*["']([^"']+)["']''', html, flags=re.I):
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://admiretheweb.com" + href
        elif not href.startswith(("http://", "https://")):
            continue
        if href not in links:
            links.append(href)
    return links


def extract_title(html):
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    if not match:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(1))).strip()


def extract_headings(html):
    headings = re.findall(
        r"(?is)<h[1-3][^>]*>(.*?)</h[1-3]>",
        html,
    )
    values = []
    for heading in headings:
        value = re.sub(r"<[^>]+>", " ", heading)
        value = re.sub(r"\s+", " ", value).strip()
        if value and value not in values:
            values.append(value)
    return values[:10]


def likely_external_website(url):
    """Accept real website destinations and reject hub/assets/social/syndication URLs."""
    blocked_hosts = {
        "admiretheweb.com",
        "fonts.googleapis.com",
        "fonts.gstatic.com",
        "googleapis.com",
        "gstatic.com",
        "feedburner.com",
        "feeds.feedburner.com",
        "instagram.com",
        "linkedin.com",
        "facebook.com",
        "pinterest.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "vimeo.com",
        "plus.google.com",
    }

    url = unescape(url.strip())

    if not url.startswith(("http://", "https://")):
        return False

    match = re.search(r"https?://([^/\s?#]+)", url)
    if not match:
        return False

    host = match.group(1).lower().removeprefix("www.")

    if any(
        host == blocked or host.endswith("." + blocked)
        for blocked in blocked_hosts
    ):
        return False

    if any(
        token in url.lower()
        for token in (
            ".css", ".js", ".woff", ".woff2", ".ttf", ".otf",
            ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif",
            ".xml", ".rss", ".atom",
        )
    ):
        return False

    return True


def extract_absolute_urls(html):
    """Extract URLs whether they are hrefs or visible text in the page."""
    html = unescape(html)
    return list(dict.fromkeys(
        re.findall(r'https?://[^"\'<>\s]+', html, flags=re.I)
    ))


def find_actual_reference_url(entry_html):
    """Extract only the submitted website from an individual Admire entry."""
    visible_html = re.sub(
        r"(?is)<(script|style|noscript|svg).*?</\1>",
        " ",
        entry_html,
    )

    for match in re.finditer(
        r"<a\b[^>]*href=[\"'](https?://[^\"']+)[\"'][^>]*>(.*?)</a>",
        visible_html,
        flags=re.I | re.S,
    ):
        href = unescape(match.group(1)).strip().rstrip(".,);]>")
        label = re.sub(r"<[^>]+>", " ", match.group(2))
        label = re.sub(r"\s+", " ", unescape(label)).strip()
        if likely_external_website(href) and re.match(r"^https?://", label, re.I):
            return href

    visible_text = clean_reference_text(visible_html, 10000)
    for url in re.findall(r"https?://[^\s<>\"']+", visible_text, flags=re.I):
        url = url.rstrip(".,);]>")
        if likely_external_website(url):
            return url

    for url in extract_reference_links(visible_html, REFERENCE_HUB_URL):
        if likely_external_website(url):
            return url

    return ""

def extract_entry_tags(html):
    """Extract a compact tag/category signal from the individual entry."""
    text_value = clean_reference_text(html, 2200).casefold()

    known_tags = [
        "professional", "service", "property", "agency",
        "natural", "earth", "minimal", "editorial",
        "fixed header", "reveal", "large footer",
        "architecture", "interior design", "portfolio",
        "dark mode", "colour", "colours",
    ]

    return [
        tag for tag in known_tags
        if tag.casefold() in text_value
    ][:8]


def discover_reference_candidates(hub_url=REFERENCE_HUB_URL):
    """
    Admire The Web is a discovery hub only.

    Strategy:
    1. Start with relevant category pages.
    2. Discover /inspiration/ entry pages.
    3. Open each individual entry.
    4. Extract the actual submitted website URL from that entry.
    5. Fetch a compact snapshot of the actual site.
    """
    category_urls = [
        "https://admiretheweb.com/category/service/",
        "https://admiretheweb.com/category/professional/",
        "https://admiretheweb.com/category/property/",
        "https://admiretheweb.com/category/agency/",
    ]

    # Keep the configured hub as a fallback/source, but do not treat it as a reference.
    pages = category_urls + [hub_url]
    inspiration_links = []

    for page_url in pages:
        try:
            page_html = fetch_reference_page(page_url, 50000)
        except Exception:
            continue

        for link in extract_reference_links(page_html, page_url):
            if "/inspiration/" not in link:
                continue
            if link not in inspiration_links:
                inspiration_links.append(link)

    candidates = []

    # More candidates gives DeepSeek meaningful choice, while snapshots stay compact.
    for entry_url in inspiration_links[:REFERENCE_LIMIT * 3]:
        try:
            entry_html = fetch_reference_page(entry_url, 24000)
            title = extract_title(entry_html)

            # Skip category/color hub pages accidentally linked as inspiration entries.
            if any(
                token in title.casefold()
                for token in (
                    "website design inspiration category",
                    "website design inspiration |",
                    "color website design inspiration",
                    "colour website design inspiration",
                )
            ):
                continue

            actual_url = find_actual_reference_url(entry_html)

            if not actual_url:
                continue

            actual_html = fetch_reference_page(actual_url, 18000)

            candidate = {
                "name": title or extract_title(actual_html),
                "hub_url": entry_url,
                "website_url": actual_url,
                "category_tags": extract_entry_tags(entry_html),
                "website_title": extract_title(actual_html),
                "website_headings": extract_headings(actual_html)[:5],
                "website_snapshot": clean_reference_text(actual_html, 500),
            }

            candidates.append(candidate)

            if len(candidates) >= REFERENCE_LIMIT:
                break

        except Exception:
            continue

    return candidates[:REFERENCE_LIMIT]


def print_reference_research(candidates):
    print(f"[inspiration] Hub: {REFERENCE_HUB_URL}")
    print(
        "[inspiration] Individual reference websites discovered: "
        f"{len(candidates)}"
    )

    for index, candidate in enumerate(candidates, 1):
        print(
            f"[inspiration] Candidate {index}: "
            f"{candidate.get('name', 'Unnamed')} -> "
            f"{candidate.get('website_url', '')}"
        )


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


def _discover_admire_entries() -> list[dict]:
    """Discover individual Admire inspiration pages, then their submitted sites."""
    import re
    from html.parser import HTMLParser
    from urllib.parse import urljoin

    category_urls = [
        f"{REFERENCE_HUB_URL}/category/agency/",
        f"{REFERENCE_HUB_URL}/category/professional/",
        f"{REFERENCE_HUB_URL}/category/service/",
        f"{REFERENCE_HUB_URL}/category/property/",
        f"{REFERENCE_HUB_URL}/category/site-of-the-day/",
    ]

    class EntryParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []

        def handle_starttag(self, tag, attrs):
            if tag != "a":
                return
            href = dict(attrs).get("href", "")
            if href:
                self.links.append(href)

    entries = []
    seen = set()

    for page_url in category_urls:
        try:
            html = fetch_reference_page(page_url, 50000)
        except Exception:
            continue

        parser = EntryParser()
        parser.feed(html)

        for href in parser.links:
            absolute = urljoin(page_url, href).rstrip("/")
            if not re.match(r"^https://admiretheweb\.com/inspiration/[^/]+$", absolute):
                continue
            if absolute in seen:
                continue

            seen.add(absolute)
            try:
                entry_html = fetch_reference_page(absolute, 24000)
            except Exception:
                continue

            site_url = _extract_submitted_site(entry_html)
            if not site_url:
                continue

            # Extract compact visible metadata from the individual entry.
            visible = re.sub(r"<[^>]+>", " ", entry_html)
            visible = re.sub(r"\s+", " ", visible).strip()

            title_match = re.search(r"<h1[^>]*>(.*?)</h1>", entry_html, re.I | re.S)
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else ""
            if not title:
                title = absolute.rstrip("/").split("/")[-1].replace("-", " ").title()

            tags = []
            for tag in re.findall(r'href="[^"]*/tag/[^"]*"[^>]*>(.*?)</a>', entry_html, re.I | re.S):
                tag = re.sub(r"<[^>]+>", "", tag).strip()
                if tag and tag not in tags:
                    tags.append(tag)

            entries.append({
                "name": title[:80],
                "entry_url": absolute,
                "site_url": site_url,
                "tags": tags[:12],
                "summary": visible[:500],
            })

            if len(entries) >= 4:
                return entries

    return entries


def _score_reference_candidate(candidate: dict, business: dict) -> int:
    """Prefer service/professional/natural visual references without forcing industry."""
    text = " ".join([
        candidate.get("name", ""),
        " ".join(candidate.get("tags", [])),
        candidate.get("summary", ""),
    ]).lower()

    score = 0
    for term in ("service", "professional", "local", "business", "responsive"):
        if term in text:
            score += 2
    for term in ("nature", "natural", "earth", "outdoor", "green", "organic"):
        if term in text:
            score += 1
    for term in ("fixed header", "hero", "large type", "grid", "hover", "reveal", "animation"):
        if term in text:
            score += 1

    return score


def get_reference_research(business: dict, handoff: dict) -> list[dict]:
    """Return a small, validated set of real websites from Admire The Web."""
    candidates = _discover_admire_entries()
    if not candidates:
        raise RuntimeError(
            f"No individual reference websites were discovered from {REFERENCE_HUB_URL}. "
            "Admire's entry structure may have changed."
        )

    candidates.sort(
        key=lambda item: _score_reference_candidate(item, business),
        reverse=True,
    )
    candidates = candidates[:4]

    print(f"[inspiration] Individual reference websites discovered: {len(candidates)}")
    for index, candidate in enumerate(candidates, 1):
        print(
            f"Candidate {index}: {candidate['name']} -> "
            f"{candidate['site_url']}"
        )

    return candidates

def generate_copy(business, handoff):
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    reference_candidates = get_reference_research(
        business,
        handoff,
    )
    print_reference_research(reference_candidates)

    compact_candidates = [
        {
            "name": item.get("name", ""),
            "website_url": item.get("website_url", ""),
            "category_tags": item.get("category_tags", [])[:6],
            "website_title": item.get("website_title", ""),
            "website_headings": item.get("website_headings", [])[:4],
            "website_snapshot": item.get("website_snapshot", "")[:500],
        }
        for item in reference_candidates
    ]

    source = json.dumps(
        {
            "business": business,
            "niche": get_niche(business, handoff),
            "ai_handoff": handoff,
            "reference_hub": {
                "name": "Admire The Web",
                "url": REFERENCE_HUB_URL,
                "purpose": "Discovery hub only. Never use the hub itself as the design reference.",
            },
            "reference_candidates": compact_candidates,
            "reference_rules": REFERENCE_HUB_RULES,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": source,
            },
        ],
        temperature=0.7,
        max_tokens=1900,
    )

    print("\nDeepSeek Usage:")
    print(response.usage)

    try:
        log_usage(
            get_business_name(business, handoff),
            response.usage,
        )
    except Exception as error:
        print(f"Usage logging skipped: {error}")

    content = response.choices[0].message.content or "{}"

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"DeepSeek returned invalid JSON: {error}"
        )

    seo = result.get("seo")

    if not isinstance(seo, dict):
        raise RuntimeError("DeepSeek did not return a valid seo object.")

    required_seo_fields = [
        "title",
        "meta_description",
        "primary_keyword",
        "secondary_keywords",
        "search_intent",
    ]

    missing_seo = [
        field
        for field in required_seo_fields
        if field not in seo
    ]

    if missing_seo:
        raise RuntimeError(
            "DeepSeek returned an incomplete seo object. "
            f"Missing: {', '.join(missing_seo)}"
        )

    design = result.get("design_spec")

    if not isinstance(design, dict):
        raise RuntimeError("DeepSeek did not return a valid design_spec.")

    required_design_fields = [
        "direction",
        "visual_style",
        "layout_style",
        "hero_style",
        "navigation_style",
        "color_direction",
        "design_system",
        "reference_selection",
        "reference_analysis",
        "reference_patterns",
        "reference_influences",
        "composition",
        "typography_style",
        "card_style",
        "button_style",
        "section_order",
        "image_strategy",
        "elementor_compatible",
        "elementor_notes",
    ]

    missing = [field for field in required_design_fields if field not in design]

    if missing:
        raise RuntimeError(
            "DeepSeek returned an incomplete design_spec. "
            f"Missing: {', '.join(missing)}"
        )

    colors = design.get("color_direction")
    if not isinstance(colors, dict):
        raise RuntimeError("DeepSeek returned an invalid color_direction.")

    required_colors = ["primary", "accent", "background", "text"]
    missing_colors = [color for color in required_colors if not colors.get(color)]

    if missing_colors:
        raise RuntimeError(
            "DeepSeek returned incomplete design colors. "
            f"Missing: {', '.join(missing_colors)}"
        )

    system = design.get("design_system")
    if not isinstance(system, dict):
        raise RuntimeError("DeepSeek returned an invalid design_system.")

    palette = system.get("palette")
    if not isinstance(palette, dict):
        raise RuntimeError("DeepSeek returned an invalid design_system palette.")

    required_palette = [
        "background", "surface", "surface_alt", "text", "muted",
        "primary", "accent", "dark", "on_primary",
    ]
    missing_palette = [key for key in required_palette if not palette.get(key)]
    if missing_palette:
        raise RuntimeError(
            "DeepSeek returned incomplete design_system colors. "
            f"Missing: {', '.join(missing_palette)}"
        )

    if not isinstance(system.get("dark_sections", []), list):
        raise RuntimeError("DeepSeek returned an invalid dark_sections list.")

    reference_selection = design.get("reference_selection")
    if not isinstance(reference_selection, dict):
        raise RuntimeError("DeepSeek returned an invalid reference_selection.")

    selected_url = str(reference_selection.get("website_url", "")).strip()
    candidate_urls = {
        str(item.get("website_url", "")).strip()
        for item in reference_candidates
    }

    if selected_url not in candidate_urls:
        raise RuntimeError(
            "DeepSeek selected a reference website that was not in the "
            "researched candidate list."
        )


    if selected_url.startswith("https://admiretheweb.com/"):
        raise RuntimeError(
            "DeepSeek selected the Admire The Web hub instead of an individual website."
        )

    reference_analysis = design.get("reference_analysis")
    if not isinstance(reference_analysis, dict):
        raise RuntimeError("DeepSeek returned an invalid reference_analysis.")

    if not isinstance(design.get("reference_influences"), list):
        raise RuntimeError("DeepSeek returned an invalid reference_influences list.")

    if not isinstance(design.get("composition"), dict):
        raise RuntimeError("DeepSeek returned an invalid composition object.")

    if design.get("elementor_compatible") is not True:
        raise RuntimeError(
            "DeepSeek returned a design that is not Elementor compatible."
        )

    print("\n[design] Design Spec validated.")
    print(f"[design] Direction: {design.get('direction')}")
    print(f"[design] Visual style: {design.get('visual_style')}")
    print(f"[design] Layout: {design.get('layout_style')}")
    print(f"[design] Hero: {design.get('hero_style')}")
    print(f"[design] Sections: {design.get('section_order')}")
    print(
        f"[reference] Selected: "
        f"{reference_selection.get('name')} -> {selected_url}"
    )
    print(f"[reference] Reason: {reference_selection.get('reason', '')}")
    print(f"[reference] Analysis: {reference_analysis}")
    print(f"[design] Reference patterns: {design.get('reference_patterns')}")
    print(f"[design] Reference influences: {design.get('reference_influences')}")
    print(f"[design] Composition: {design.get('composition')}")

    return result


def get_verified_services(business, handoff):
    """Return only services explicitly present in the verified source data."""
    candidates = []

    for source in (business, handoff):
        if not isinstance(source, dict):
            continue

        for key in ("services", "service_list", "service_offerings"):
            value = source.get(key)
            if isinstance(value, list):
                candidates.extend(value)

    verified = []
    for item in candidates:
        if isinstance(item, str) and item.strip():
            verified.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("name") or item.get("title") or item.get("service")
            if name and str(name).strip():
                verified.append(str(name).strip())

    return verified


def filter_services(copy_services, verified_services):
    """Keep AI services only when the source explicitly verifies them."""
    if not verified_services:
        return []

    allowed = {item.casefold() for item in verified_services}
    filtered = []

    for item in copy_services if isinstance(copy_services, list) else []:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("title") or item.get("service")
        if name and str(name).casefold() in allowed:
            filtered.append(item)

    return filtered




CSS = r"""
:root {
    --bg: #07111f;
    --bg-soft: #0d1b2e;
    --card: #101f33;
    --text: #f7f9fc;
    --muted: #aeb9c9;
    --gold: #d7b56d;
    --gold-light: #f1d99a;
    --border: rgba(255,255,255,.12);
    --max: 1180px;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    color: var(--text);
    background: var(--bg);
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.6;
}

a {
    color: inherit;
    text-decoration: none;
}

.container {
    width: min(92%, var(--max));
    margin: auto;
}

.header {
    position: sticky;
    top: 0;
    z-index: 10;
    border-bottom: 1px solid var(--border);
    background: rgba(7,17,31,.94);
    backdrop-filter: blur(12px);
}

.nav {
    min-height: 76px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 25px;
}

.logo {
    max-width: 300px;
    font-size: 19px;
    font-weight: 900;
}

nav {
    display: flex;
    gap: 24px;
}

nav a {
    color: var(--muted);
    font-size: 14px;
}

nav a:hover,
nav a:focus {
    color: var(--text);
}

.button {
    min-height: 50px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 23px;
    border-radius: 7px;
    font-weight: 900;
    transition: .2s ease;
}

.button:hover,
.button:focus {
    transform: translateY(-2px);
}

.primary {
    background: var(--gold);
    color: #07111f;
    box-shadow: 0 15px 35px rgba(215,181,109,.18);
}

.secondary {
    border: 1px solid var(--border);
    background: rgba(255,255,255,.04);
}

.hero {
    position: relative;
    overflow: hidden;
    min-height: 700px;
    display: flex;
    align-items: center;
    background:
        radial-gradient(
            circle at 80% 30%,
            rgba(215,181,109,.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 15% 85%,
            rgba(39,93,150,.25),
            transparent 35%
        ),
        linear-gradient(135deg,#07111f,#0c1c31);
}

.hero-pattern {
    position: absolute;
    width: 600px;
    height: 600px;
    right: -250px;
    top: 50px;
    border: 1px solid rgba(215,181,109,.2);
    border-radius: 50%;
    box-shadow:
        0 0 0 80px rgba(215,181,109,.025),
        0 0 0 160px rgba(215,181,109,.018);
}

.hero-grid {
    position: relative;
    display: grid;
    grid-template-columns: 1.1fr .9fr;
    gap: 70px;
    align-items: center;
}

.hero-content {
    position: relative;
}

.eyebrow {
    display: inline-block;
    margin-bottom: 18px;
    color: var(--gold);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .18em;
}

h1 {
    max-width: 850px;
    margin: 0;
    font-size: clamp(48px,7vw,86px);
    line-height: .98;
    letter-spacing: -.06em;
}

h2 {
    margin: 0;
    font-size: clamp(34px,5vw,58px);
    line-height: 1.05;
    letter-spacing: -.05em;
}

h3 {
    margin: 0;
    font-size: 21px;
}

.hero-copy {
    max-width: 700px;
    margin: 30px 0;
    color: var(--muted);
    font-size: 20px;
}

.actions {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
}

.location {
    margin-top: 25px;
    color: var(--muted);
}

.hero-visual {
    position: relative;
    min-height: 430px;
}

.hero-photo {
    position: absolute;
    inset: 0 20px 55px 0;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 24px;
    background: #101f33;
    box-shadow: 0 30px 80px rgba(0,0,0,.35);
}

.hero-photo img {
    width: 100%;
    height: 100%;
    display: block;
    object-fit: cover;
}

.hero-photo::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, transparent 35%, rgba(7,17,31,.72));
}

.photo-overlay {
    position: absolute;
    left: 24px;
    bottom: 22px;
    z-index: 1;
    color: var(--gold-light);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .12em;
}

.image-feature-section {
    padding: 95px 0;
    background: #0d1b2e;
}

.image-feature-grid {
    display: grid;
    grid-template-columns: .85fr 1.15fr;
    gap: 60px;
    align-items: center;
}

.image-feature-copy p {
    max-width: 650px;
    color: var(--muted);
    font-size: 18px;
    line-height: 1.8;
}

.image-feature {
    margin: 0;
}

.image-feature img {
    width: 100%;
    height: 390px;
    display: block;
    object-fit: cover;
    border: 1px solid var(--border);
    border-radius: 20px;
}

.image-feature figcaption {
    margin-top: 9px;
    color: var(--muted);
    font-size: 11px;
}

.visual-main,
.visual-small {
    position: absolute;
    border: 1px solid var(--border);
    border-radius: 22px;
    background: linear-gradient(
        145deg,
        rgba(255,255,255,.11),
        rgba(255,255,255,.025)
    );
    box-shadow: 0 30px 80px rgba(0,0,0,.35);
}

.visual-main {
    inset: 20px 30px 70px 0;
    padding: 45px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.visual-main span {
    color: var(--muted);
    font-size: 30px;
    font-weight: 900;
}

.visual-main strong {
    color: var(--gold);
    font-size: clamp(55px,6vw,82px);
    line-height: .9;
}

.visual-small {
    right: 0;
    bottom: 0;
    padding: 23px;
    color: var(--gold-light);
    font-size: 13px;
    font-weight: 900;
    letter-spacing: .08em;
}

.intro-section {
    padding: 95px 0;
    border-bottom: 1px solid var(--border);
}

.intro-grid,
.local-grid {
    display: grid;
    grid-template-columns: .8fr 1.2fr;
    gap: 80px;
    align-items: center;
}

.intro-copy,
.local-copy {
    color: var(--muted);
    font-size: 20px;
    line-height: 1.8;
}

.section {
    padding: 115px 0;
}

.section-heading {
    max-width: 820px;
}

.section-heading p {
    margin-top: 22px;
    color: var(--muted);
    font-size: 18px;
}

.service-grid {
    display: grid;
    grid-template-columns: repeat(2,1fr);
    gap: 18px;
    margin-top: 50px;
}

.service-card {
    min-height: 250px;
    padding: 35px;
    border: 1px solid var(--border);
    border-radius: 18px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.08),
            rgba(255,255,255,.025)
        );
    transition: transform .25s ease,border-color .25s ease;
}

.service-card:hover {
    transform: translateY(-5px);
    border-color: rgba(215,181,109,.45);
}

.service-number {
    color: var(--gold);
    font-weight: 900;
    letter-spacing: .1em;
}

.service-card h3 {
    margin-top: 75px;
}

.service-card p,
.process-card p {
    color: var(--muted);
}

.dark {
    background: var(--bg-soft);
}

.about-grid {
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: 60px;
}

.about-number {
    color: rgba(215,181,109,.15);
    font-size: 100px;
    font-weight: 900;
    line-height: 1;
}

.large-copy {
    max-width: 820px;
    color: var(--muted);
    font-size: 21px;
    line-height: 1.8;
}

.benefit-grid {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 16px;
    margin-top: 50px;
}

.benefit-card {
    min-height: 190px;
    padding: 28px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: rgba(255,255,255,.04);
}

.benefit-number {
    color: var(--gold);
    font-weight: 900;
}

.process-section {
    background: #091526;
}

.process-grid {
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 16px;
    margin-top: 50px;
}

.process-card {
    padding: 35px;
    border-top: 2px solid var(--gold);
    background: rgba(255,255,255,.04);
}

.process-card > span {
    color: var(--gold);
    font-weight: 900;
}

.process-card h3 {
    margin-top: 45px;
}

.local-section {
    padding: 105px 0;
    background:
        radial-gradient(
            circle at 85% 50%,
            rgba(215,181,109,.13),
            transparent 30%
        ),
        #0b1829;
}

.location-box {
    margin-top: 25px;
    padding: 25px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: rgba(255,255,255,.04);
}

.location-box h3 {
    color: var(--text);
}

.faq {
    max-width: 900px;
    margin-top: 45px;
    display: grid;
    gap: 12px;
}

details {
    padding: 23px 26px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: rgba(255,255,255,.04);
}

summary {
    cursor: pointer;
    font-weight: 900;
}

details p {
    color: var(--muted);
}

.cta-section {
    padding: 105px 0;
}

.cta-box {
    padding: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 50px;
    border: 1px solid var(--border);
    border-radius: 24px;
    background:
        radial-gradient(
            circle at 90% 20%,
            rgba(215,181,109,.2),
            transparent 35%
        ),
        linear-gradient(135deg,#13243a,#081321);
}

.cta-box p {
    max-width: 650px;
    color: var(--muted);
    font-size: 18px;
}

.cta-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
}

.footer {
    padding: 40px 0;
    border-top: 1px solid var(--border);
}

.footer-grid {
    display: flex;
    justify-content: space-between;
    gap: 30px;
}

.footer p {
    color: var(--muted);
}

:focus-visible {
    outline: 2px solid var(--gold);
    outline-offset: 4px;
}

@media (max-width: 850px) {

    nav {
        display: none;
    }

    .hero {
        min-height: 650px;
    }

    .hero-grid,
    .intro-grid,
    .about-grid,
    .local-grid,
    .service-grid,
    .benefit-grid,
    .process-grid {
        grid-template-columns: 1fr;
    }

    .hero-visual {
        min-height: 300px;
    }

    .visual-main strong {
        font-size: 55px;
    }

    .section {
        padding: 80px 0;
    }

    .cta-box {
        padding: 35px;
        flex-direction: column;
        align-items: flex-start;
    }

    .footer-grid {
        flex-direction: column;
    }
}

@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }

    *,
    *::before,
    *::after {
        animation-duration: .01ms !important;
        transition-duration: .01ms !important;
    }
}
"""


def build_design_css(design):
    """Translate the AI design system into one coherent renderer theme."""
    colors = design.get("color_direction", {})
    system = design.get("design_system", {})
    palette = system.get("palette", {}) if isinstance(system, dict) else {}
    if not isinstance(colors, dict):
        colors = {}
    if not isinstance(palette, dict):
        palette = {}

    def safe_color(value, fallback):
        value = str(value or "").strip()
        if (
            len(value) == 7
            and value.startswith("#")
            and all(char in "0123456789abcdefABCDEF" for char in value[1:])
        ):
            return value
        return fallback

    background = safe_color(
        palette.get("background"),
        safe_color(colors.get("background"), "#f4f1e9"),
    )
    surface = safe_color(palette.get("surface"), "#ffffff")
    surface_alt = safe_color(palette.get("surface_alt"), "#eef2ef")
    text = safe_color(
        palette.get("text"),
        safe_color(colors.get("text"), "#172019"),
    )
    muted = safe_color(palette.get("muted"), "#5f6b64")
    primary = safe_color(
        palette.get("primary"),
        safe_color(colors.get("primary"), "#20513a"),
    )
    accent = safe_color(
        palette.get("accent"),
        safe_color(colors.get("accent"), "#b58a4a"),
    )
    dark = safe_color(palette.get("dark"), "#10271e")
    on_primary = safe_color(palette.get("on_primary"), "#ffffff")

    typography = str(design.get("typography_style", "")).lower()
    heading_font = (
        "Georgia, 'Times New Roman', serif"
        if any(word in typography for word in ("serif", "editorial", "classic", "luxury"))
        else "Arial, Helvetica, sans-serif"
    )
    body_font = (
        "Trebuchet MS, Arial, sans-serif"
        if any(word in typography for word in ("humanist", "warm", "organic"))
        else "Arial, Helvetica, sans-serif"
    )

    spacing = str(system.get("spacing", "comfortable")).lower()
    spacing_map = {
        "compact": ("clamp(58px, 6vw, 82px)", "clamp(44px, 5vw, 68px)"),
        "spacious": ("clamp(76px, 7vw, 108px)", "clamp(58px, 6vw, 84px)"),
        "comfortable": ("clamp(66px, 6.5vw, 92px)", "clamp(50px, 5.5vw, 74px)"),
    }
    section_space, compact_space = spacing_map.get(spacing, spacing_map["comfortable"])

    container = str(system.get("container", "wide")).lower()
    max_width = "1240px" if container == "wide" else "1120px"
    radius = str(system.get("radius", "medium")).lower()
    radius_value = {"small": "8px", "large": "24px"}.get(radius, "14px")
    shadow = str(system.get("shadow", "soft")).lower()
    shadow_value = (
        "none"
        if shadow in ("none", "flat")
        else "0 14px 38px rgba(20,30,24,.09)"
    )

    return f"""
:root {{
    --bg: {background};
    --surface: {surface};
    --surface-alt: {surface_alt};
    --text: {text};
    --muted: {muted};
    --primary: {primary};
    --accent: {accent};
    --dark: {dark};
    --on-primary: {on_primary};
    --border: color-mix(in srgb, var(--text) 12%, transparent);
    --font-body: {body_font};
    --font-heading: {heading_font};
    --section-space: {section_space};
    --compact-space: {compact_space};
    --max: {max_width};
    --radius: {radius_value};
    --shadow: {shadow_value};
    --gold: var(--accent);
    --gold-light: color-mix(in srgb, var(--accent) 55%, white);
}}

html {{ scroll-behavior: smooth; }}
body {{ font-family: var(--font-body); color: var(--text); background: var(--bg); }}
h1, h2, h3, h4, .logo, .button {{ font-family: var(--font-heading); }}
h1, h2, h3, h4 {{ color: var(--text); letter-spacing: -.025em; }}
.container {{ width: min(calc(100% - 40px), var(--max)); margin-inline: auto; }}
.header {{ background: color-mix(in srgb, var(--surface) 94%, transparent); border-color: var(--border); backdrop-filter: blur(14px); position: sticky; top: 0; z-index: 50; transition: box-shadow .25s ease, background-color .25s ease; }}
.header.is-scrolled {{ box-shadow: 0 8px 28px rgba(20,30,24,.08); }}
nav a {{ color: var(--muted); transition: color .2s ease; }}
nav a:hover, nav a:focus {{ color: var(--primary); }}
.button {{ border-radius: 999px; transition: transform .22s ease, background-color .22s ease, color .22s ease, border-color .22s ease, box-shadow .22s ease; }}
.button.primary {{ background: var(--primary); color: var(--on-primary); box-shadow: 0 8px 24px color-mix(in srgb, var(--primary) 24%, transparent); }}
.button.primary:hover {{ transform: translateY(-2px); box-shadow: 0 12px 30px color-mix(in srgb, var(--primary) 30%, transparent); }}
.button.secondary {{ border-color: var(--border); background: var(--surface); color: var(--text); }}
.button.secondary:hover {{ border-color: var(--primary); color: var(--primary); transform: translateY(-2px); }}
.eyebrow, .service-number, .benefit-number, .process-card > span {{ color: var(--primary); }}
.rendered-main > .section, .local-section, .cta-section {{ background: var(--bg); color: var(--text); }}
.tone-light {{ background: var(--bg) !important; color: var(--text); }}
.tone-dark {{ background: var(--dark) !important; color: #fff !important; }}
.tone-dark h1, .tone-dark h2, .tone-dark h3, .tone-dark h4 {{ color: #fff; }}
.tone-dark p, .tone-dark .large-copy, .tone-dark .section-heading p {{ color: rgba(255,255,255,.76); }}
.tone-dark .eyebrow, .tone-dark .service-number, .tone-dark .benefit-number, .tone-dark .process-card > span {{ color: var(--accent); }}
.section {{ padding: var(--section-space) 0; }}
.section + .section {{ padding-top: var(--compact-space); }}
.section-heading {{ max-width: 780px; margin-bottom: 38px; }}
.section-heading h2 {{ max-width: 720px; }}
.section-heading p {{ max-width: 650px; }}
.about-grid {{ align-items: center; }}
.about-grid .about-number {{ align-self: start; }}
.about-grid .large-copy {{ max-width: 690px; }}
.about-grid .about-image {{ margin-top: 34px; }}
.about-image img {{ width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block; border-radius: var(--radius); box-shadow: var(--shadow); }}
.about-support {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-top: 30px; }}
.about-support-item {{ border-top: 2px solid var(--accent); padding-top: 14px; }}
.about-support-item strong {{ display: block; margin-bottom: 6px; }}
.about-support-item span {{ color: var(--muted); font-size: 14px; line-height: 1.55; }}
.service-grid {{ grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-top: 34px; }}
.service-card {{ min-height: 0; padding: 30px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow); transition: transform .28s ease, box-shadow .28s ease, border-color .28s ease; }}
.service-card:hover {{ transform: translateY(-5px); box-shadow: 0 22px 50px rgba(20,30,24,.12); border-color: color-mix(in srgb, var(--primary) 50%, var(--border)); }}
.service-card h3 {{ margin-top: 28px; }}
.service-card p, .benefit-card p, .process-card p, .section-heading p, .large-copy, .intro-copy, .local-copy, .cta-box p, details p, .footer p {{ color: var(--muted); }}
.service-support {{ margin-top: 24px; padding: 26px 30px; border-left: 3px solid var(--accent); background: color-mix(in srgb, var(--primary) 6%, var(--surface)); }}
.service-support strong {{ display: block; margin-bottom: 8px; }}
.service-support p {{ margin: 0; color: var(--muted); max-width: 760px; }}
.benefit-grid {{ grid-template-columns: repeat(4, 1fr); gap: 0; border-top: 1px solid var(--border); border-left: 1px solid var(--border); }}
.benefit-card {{ padding: 26px 24px; background: var(--surface); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
.process-grid {{ grid-template-columns: repeat(3, 1fr); gap: 0; border-top: 1px solid var(--border); border-left: 1px solid var(--border); }}
.process-card {{ padding: 28px; background: var(--surface); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); min-height: 190px; }}
.process-card h3 {{ margin-top: 30px; }}
.local-section {{ border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
.local-grid {{ align-items: center; }}
.local-copy {{ max-width: 620px; }}
.location-box {{ margin-top: 24px; padding: 20px 22px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }}
.location-box h3 {{ margin-top: 8px; font-size: 17px; }}
details {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 10px; overflow: hidden; }}
details summary {{ padding: 20px 22px; cursor: pointer; font-weight: 700; list-style: none; }}
details summary::-webkit-details-marker {{ display: none; }}
details summary::after {{ content: '+'; float: right; color: var(--primary); font-size: 20px; }}
details[open] summary::after {{ content: '−'; }}
details p {{ padding: 0 22px 20px; margin: 0; }}
.faq {{ max-width: 900px; }}
.cta-section {{ padding: var(--section-space) 0; background: var(--dark) !important; }}
.cta-box {{ padding: clamp(34px, 5vw, 60px); display: flex; align-items: center; justify-content: space-between; gap: 45px; border: 1px solid rgba(255,255,255,.14); border-radius: calc(var(--radius) + 4px); background: color-mix(in srgb, var(--dark) 88%, var(--primary)); box-shadow: 0 20px 60px rgba(0,0,0,.18); }}
.cta-box h2 {{ color: #fff; max-width: 720px; }}
.cta-box p {{ color: rgba(255,255,255,.76); max-width: 650px; }}
.cta-box .button.secondary {{ background: rgba(255,255,255,.08); border-color: rgba(255,255,255,.22); color: #fff; }}
.footer {{ padding: 34px 0; border-top: 1px solid var(--border); background: var(--surface); }}
.footer-grid {{ align-items: center; }}
.hero {{ background: var(--dark); }}
.hero-full-bleed {{ min-height: min(720px, 82vh); display: grid; align-items: center; position: relative; overflow: hidden; }}
.hero-full-bleed .hero-background {{ position: absolute; inset: 0; }}
.hero-full-bleed .hero-background img {{ width: 100%; height: 100%; object-fit: cover; display: block; animation: heroZoom 14s ease-out both; }}
.hero-full-bleed .hero-overlay {{ position: absolute; inset: 0; background: linear-gradient(90deg, color-mix(in srgb, var(--dark) 82%, transparent), color-mix(in srgb, var(--dark) 40%, transparent) 62%, color-mix(in srgb, var(--dark) 22%, transparent)); }}
.hero-full-bleed .hero-content-overlay {{ position: relative; z-index: 1; max-width: 900px; padding-block: 90px; }}
.hero-full-bleed .hero-content-overlay .hero-copy {{ max-width: 720px; margin: 20px 0 28px; }}
.hero-full-bleed .hero-content-overlay h1, .hero-full-bleed .hero-content-overlay .hero-copy, .hero-full-bleed .hero-content-overlay .location {{ color: #fff; }}
.hero-full-bleed .hero-content-overlay .eyebrow {{ color: var(--accent); }}
.hero-full-bleed .hero-content-overlay .actions {{ justify-content: flex-start; }}
.hero-overlap {{ padding: var(--section-space) 0; }}
.hero-overlap .hero-grid {{ align-items: center; }}
.hero-panel {{ position: relative; z-index: 2; padding: clamp(32px, 5vw, 70px); background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); }}
.hero-overlap-visual {{ margin-left: -8%; }}
.hero-overlap-visual .hero-photo img {{ width: 100%; height: 560px; object-fit: cover; border-radius: var(--radius); display: block; }}
.hero-copy {{ color: var(--muted); }}
.hero-photo {{ overflow: hidden; }}
.image-feature img, .hero-photo img {{ transition: transform .8s ease; }}
.hero-photo:hover img, .image-feature:hover img {{ transform: scale(1.025); }}
.composition-editorial .section-heading {{ max-width: 920px; }}
.composition-asymmetric .container {{ max-width: 1160px; }}
.composition-feature-grid .benefit-card {{ min-height: 170px; }}
.composition-split-media .about-grid, .composition-split-media.local-section .local-grid {{ grid-template-columns: minmax(150px,.45fr) minmax(0,1.55fr); }}
.reveal {{ will-change: transform, opacity; }}
.js-enabled .reveal {{ opacity: 0; transform: translateY(18px); transition: opacity .65s ease, transform .65s ease; }}
.js-enabled .reveal.is-visible {{ opacity: 1; transform: none; }}
.menu-toggle {{ display: none; border: 1px solid var(--border); background: var(--surface); color: var(--text); border-radius: 999px; padding: 10px 14px; font: inherit; cursor: pointer; }}
@keyframes heroZoom {{ from {{ transform: scale(1.035); }} to {{ transform: scale(1); }} }}
@media (max-width: 900px) {{
    .benefit-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .process-grid {{ grid-template-columns: 1fr; }}
    .about-support {{ grid-template-columns: 1fr; }}
    .hero-overlap-visual {{ margin-left: 0; }}
    .hero-overlap .hero-grid {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 850px) {{
    .menu-toggle {{ display: inline-flex; align-items: center; justify-content: center; }}
    .site-nav {{ display: none; position: absolute; left: 20px; right: 20px; top: calc(100% + 8px); padding: 12px; flex-direction: column; gap: 2px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }}
    .site-nav.is-open {{ display: flex; }}
    .site-nav a {{ padding: 11px 10px; }}
    .nav {{ position: relative; min-height: 66px; }}
    .header > .container {{ gap: 12px; }}
    .header .button {{ padding: 10px 14px; }}
    .hero-full-bleed {{ min-height: 620px; }}
    .hero-full-bleed .hero-content-overlay {{ padding-block: 72px; }}
    .hero-overlap-visual .hero-photo img {{ height: 360px; }}
    .about-grid {{ grid-template-columns: 1fr; gap: 22px; }}
    .about-grid .about-number {{ order: -1; }}
    .local-grid {{ grid-template-columns: 1fr; gap: 28px; }}
    .benefit-grid {{ grid-template-columns: 1fr; }}
    .cta-box {{ flex-direction: column; align-items: flex-start; }}
}}
@media (max-width: 560px) {{
    .container {{ width: min(calc(100% - 28px), var(--max)); }}
    .section {{ padding: 58px 0; }}
    .section + .section {{ padding-top: 44px; }}
    .hero-full-bleed {{ min-height: 580px; }}
    .hero-full-bleed .hero-content-overlay {{ padding-block: 58px; }}
    .hero-full-bleed .hero-overlay {{ background: linear-gradient(90deg, color-mix(in srgb, var(--dark) 78%, transparent), color-mix(in srgb, var(--dark) 52%, transparent)); }}
    .service-grid {{ grid-template-columns: 1fr; }}
    .cta-box {{ padding: 30px 24px; }}
}}
@media (prefers-reduced-motion: reduce) {{
    html {{ scroll-behavior: auto; }}
    .js-enabled .reveal, .js-enabled .reveal.is-visible {{ opacity: 1; transform: none; transition: none; }}
    .hero-full-bleed .hero-background img {{ animation: none; }}
}}
"""


def build_html(business, copy, niche, output_dir, handoff=None):
    name = get_business_name(business, {})
    phone = business.get("phone", "")
    address = business.get("address", "")
    website = business.get("website", "")
    verified_services = get_verified_services(business, handoff or {})

    design = copy.get("design_spec", {})
    if not isinstance(design, dict):
        design = {}
    design_css = build_design_css(design)
    hero_style = str(design.get("hero_style", "")).lower()
    section_order = design.get("section_order", [])
    if not isinstance(section_order, list):
        section_order = []

    allowed_sections = {
        "hero",
        "about",
        "services",
        "benefits",
        "process",
        "local",
        "faq",
        "cta",
    }
    order = []
    for section in section_order:
        key = str(section).strip().lower()
        if key in allowed_sections and key not in order:
            order.append(key)

    if not order:
        order = ["hero", "about", "services", "benefits", "process", "local", "faq", "cta"]

    system = design.get("design_system", {})
    if not isinstance(system, dict):
        system = {}
    dark_sections = system.get("dark_sections", [])
    if not isinstance(dark_sections, list):
        dark_sections = []
    dark_sections = {str(item).strip().lower() for item in dark_sections}

    composition = design.get("composition", {})
    if not isinstance(composition, dict):
        composition = {}

    def composition_class(key):
        value = str(composition.get(key, "")).strip().lower()
        value = "-".join(value.split())
        allowed = {
            "split-media", "editorial", "asymmetric", "feature-grid",
            "steps", "split-dark", "accordion", "contained-cta",
            "stacked", "minimal", "grid"
        }
        return f"composition-{value}" if value in allowed else ""

    def tone_class(key, base):
        tone = "tone-dark" if key in dark_sections else "tone-light"
        comp = composition_class(key)
        return " ".join(part for part in (base, tone, comp) if part)

    image_queries = copy.get("image_queries", [])
    if not isinstance(image_queries, list):
        image_queries = []
    image_queries = [str(x).strip() for x in image_queries if str(x).strip()]
    image_queries = (
        image_queries
        + [f"professional {niche} service", f"local {niche} business"]
    )[:2]

    image_alt = copy.get("image_alt", [])
    if not isinstance(image_alt, list):
        image_alt = []
    image_alt = [str(x).strip() for x in image_alt if str(x).strip()]
    image_alt = (
        image_alt
        + [f"Professional {niche} service", f"Local {niche} business"]
    )[:2]

    images_dir = Path(output_dir) / "images"

    hero_image = download_stock_image(
        image_queries[0],
        images_dir,
        "hero",
    )
    secondary_image = download_stock_image(
        image_queries[1],
        images_dir,
        "secondary",
    )

    hero_image = f"images/{hero_image}"
    secondary_image = f"images/{secondary_image}"

    niche_label = escape(str(niche)).upper()
    niche_title = escape(str(niche))

    headline = copy.get(
        "headline",
        f"Professional {niche} Service in Your Area",
    )
    subheadline = copy.get("subheadline", "")
    intro = copy.get("intro", "")
    about_title = copy.get(
        "about_title",
        f"Local {niche} Made Simple",
    )
    about = copy.get("about", "")
    services_intro = copy.get("services_intro", "")
    services = filter_services(
        copy.get("services", []),
        verified_services,
    )
    benefits = copy.get("benefits", [])
    process = copy.get("process", [])
    local_intro = copy.get("local_intro", "")
    faq = copy.get("faq", [])
    cta_title = copy.get("cta_title", "Ready to Get Started?")
    cta_text = copy.get("cta_text", "")

    seo = copy.get("seo", {})
    seo_title = str(
        seo.get("title") or f"{name} | {niche}"
    ).strip()
    meta_description = str(
        seo.get("meta_description") or subheadline or intro
    ).strip()
    primary_keyword = str(
        seo.get("primary_keyword") or niche
    ).strip()

    phone_html = phone_link(phone)

    services_html = ""
    for index, service in enumerate(services[:8], 1):
        if not isinstance(service, dict):
            continue

        service_name = service.get("name", "")
        description = service.get("description", "")

        if service_name and description:
            services_html += f"""
            <article class="service-card">
                <span class="service-number">{index:02d}</span>
                <h3>{escape(str(service_name))}</h3>
                <p>{escape(str(description))}</p>
            </article>
            """

    if not services_html:
        services_html = f"""
        <article class="service-card">
            <span class="service-number">01</span>
            <h3>{niche_title} Services</h3>
            <p>
                Contact the business directly to discuss your needs and determine
                the appropriate service for your situation.
            </p>
        </article>
        """

    benefits_html = ""
    for index, benefit in enumerate(benefits[:4], 1):
        if isinstance(benefit, dict):
            benefit_title = benefit.get("title") or benefit.get("name") or ""
            benefit_text = benefit.get("text") or benefit.get("description") or ""
        else:
            benefit_title = str(benefit).strip() if benefit else ""
            benefit_text = ""

        if benefit_title:
            benefits_html += f"""
            <article class="benefit-card">
                <span class="benefit-number">{index:02d}</span>
                <div>
                    <h3>{escape(str(benefit_title))}</h3>
                    {f'<p>{escape(str(benefit_text))}</p>' if benefit_text else ""}
                </div>
            </article>
            """

    process_html = ""
    for index, item in enumerate(process[:3], 1):
        if not isinstance(item, dict):
            continue

        title = item.get("title", "")
        text = item.get("text", "")

        if title and text:
            process_html += f"""
            <article class="process-card">
                <span>{index:02d}</span>
                <h3>{escape(str(title))}</h3>
                <p>{escape(str(text))}</p>
            </article>
            """

    faq_html = ""
    for item in faq[:5]:
        if not isinstance(item, dict):
            continue

        question = item.get("question", "")
        answer = item.get("answer", "")

        if question and answer:
            faq_html += f"""
            <details>
                <summary>{escape(str(question))}</summary>
                <p>{escape(str(answer))}</p>
            </details>
            """

    location_html = ""
    if address:
        location_html = f"""
        <div class="location-box">
            <span class="eyebrow">LOCAL LOCATION</span>
            <h3>{escape(str(address))}</h3>
        </div>
        """

    website_html = ""
    if website:
        website_html = f"""
        <a class="button secondary"
           href="{escape(str(website))}"
           target="_blank"
           rel="noopener">
            Visit Website
        </a>
        """

    # Phase 2B: the hero renderer follows the AI hero_style.
    hero_mode = "split"
    if any(term in hero_style for term in (
        "full-width", "full width", "full-bleed", "background image"
    )):
        hero_mode = "full-bleed"
    elif any(term in hero_style for term in (
        "overlap", "offset", "panel"
    )):
        hero_mode = "overlap"

    hero_section = ""
    if hero_mode == "full-bleed":
        hero_section = f"""
        <section data-section="hero" class="hero hero-full-bleed">
            <div class="hero-background">
                <img src="{escape(hero_image, quote=True)}"
                     alt="{escape(image_alt[0], quote=True)}"
                     loading="eager">
            </div>
            <div class="hero-overlay"></div>
            <div class="container hero-content hero-content-overlay">
                <span class="eyebrow">{niche_label}</span>
                <h1>{escape(str(headline))}</h1>
                <p class="hero-copy">{escape(str(subheadline))}</p>
                <div class="actions">
                    {phone_html}
                    <a class="button secondary" href="#contact">Get Started</a>
                </div>
                {f'<p class="location">{escape(str(address))}</p>' if address else ""}
            </div>
        </section>
        """
    elif hero_mode == "overlap":
        hero_section = f"""
        <section data-section="hero" class="hero hero-overlap">
            <div class="container hero-grid">
                <div class="hero-content hero-panel">
                    <span class="eyebrow">{niche_label}</span>
                    <h1>{escape(str(headline))}</h1>
                    <p class="hero-copy">{escape(str(subheadline))}</p>
                    <div class="actions">
                        {phone_html}
                        <a class="button secondary" href="#contact">Get Started</a>
                    </div>
                    {f'<p class="location">{escape(str(address))}</p>' if address else ""}
                </div>
                <div class="hero-visual hero-overlap-visual">
                    <div class="hero-photo">
                        <img src="{escape(hero_image, quote=True)}"
                             alt="{escape(image_alt[0], quote=True)}"
                             loading="eager">
                    </div>
                </div>
            </div>
        </section>
        """
    else:
        hero_section = f"""
        <section data-section="hero" class="hero">
            <div class="container hero-grid">
                <div class="hero-content">
                    <span class="eyebrow">{niche_label}</span>
                    <h1>{escape(str(headline))}</h1>
                    <p class="hero-copy">{escape(str(subheadline))}</p>
                    <div class="actions">
                        {phone_html}
                        <a class="button secondary" href="#contact">Get Started</a>
                    </div>
                    {f'<p class="location">{escape(str(address))}</p>' if address else ""}
                </div>
                <div class="hero-visual">
                    <div class="hero-photo">
                        <img src="{escape(hero_image, quote=True)}"
                             alt="{escape(image_alt[0], quote=True)}"
                             loading="eager">
                        <div class="photo-overlay">{niche_label}</div>
                    </div>
                </div>
            </div>
        </section>
        """

    sections = {
        "hero": hero_section,
        "about": f"""
        <section data-section="about" id="about" class="{tone_class('about', 'section')}">
            <div class="container about-grid">
                <div class="about-number">01</div>
                <div>
                    <span class="eyebrow">ABOUT</span>
                    <h2>{escape(str(about_title))}</h2>
                    {f'<p class="intro-copy">{escape(str(intro))}</p>' if intro else ''}
                    <p class="large-copy">{escape(str(about))}</p>
                    <div class="about-image image-feature">
                        <img src="{escape(secondary_image, quote=True)}" alt="{escape(image_alt[1], quote=True)}" loading="lazy">
                    </div>
                    <div class="about-support">
                        <div class="about-support-item"><strong>Plan the work</strong><span>Clarify the property, the work needed, access, and the outcome you want before service begins.</span></div>
                        <div class="about-support-item"><strong>Protect the property</strong><span>Good tree-care planning considers people, structures, landscaping, and safe work areas.</span></div>
                        <div class="about-support-item"><strong>Know the next step</strong><span>Clear communication helps you understand what happens before, during, and after the job.</span></div>
                    </div>
                </div>
            </div>
        </section>
        """,
        "services": f"""
        <section data-section="services" id="services" class="{tone_class('services', 'section')}">
            <div class="container">
                <div class="section-heading">
                    <span class="eyebrow">{niche_label} SERVICES</span>
                    <h2>Services Built Around Your Needs</h2>
                    <p>{escape(str(services_intro))}</p>
                </div>
                <div class="service-grid">{services_html}</div>
                <div class="service-support">
                    <strong>Before choosing a tree-care service</strong>
                    <p>Consider the condition of the tree, the work area, nearby structures, access for equipment, debris handling, and the result you want. A clear scope makes it easier to discuss the right service for the property.</p>
                </div>
            </div>
        </section>
        """,
        "benefits": f"""
        <section data-section="benefits" class="{tone_class('benefits', 'section')}">
            <div class="container">
                <div class="section-heading">
                    <span class="eyebrow">WHY IT MATTERS</span>
                    <h2>Service Built Around Your Needs</h2>
                </div>
                <div class="benefit-grid">{benefits_html}</div>
            </div>
        </section>
        """,
        "process": f"""
        <section data-section="process" id="process" class="{tone_class('process', 'section process-section')}">
            <div class="container">
                <div class="section-heading">
                    <span class="eyebrow">HOW IT WORKS</span>
                    <h2>Simple Steps. Clear Process.</h2>
                </div>
                <div class="process-grid">{process_html}</div>
            </div>
        </section>
        """,
        "local": f"""
        <section data-section="local" class="{tone_class('local', 'local-section')}">
            <div class="container local-grid">
                <div>
                    <span class="eyebrow">{niche_label}</span>
                    <h2>Local Service When You Need It</h2>
                </div>
                <div class="local-copy">
                    <p>{escape(str(local_intro))}</p>
                    {location_html}
                </div>
            </div>
        </section>
        """,
        "faq": f"""
        <section data-section="faq" id="faq" class="{tone_class('faq', 'section faq-section')}">
            <div class="container">
                <div class="section-heading">
                    <span class="eyebrow">FAQ</span>
                    <h2>{niche_title} Questions</h2>
                </div>
                <div class="faq">{faq_html}</div>
            </div>
        </section>
        """ if faq_html else "",
        "cta": f"""
        <section data-section="cta" id="contact" class="{tone_class('cta', 'cta-section')}">
            <div class="container cta-box">
                <div>
                    <span class="eyebrow">GET STARTED</span>
                    <h2>{escape(str(cta_title))}</h2>
                    <p>{escape(str(cta_text))}</p>
                </div>
                <div class="cta-actions">
                    {phone_html}
                    {website_html}
                </div>
            </div>
        </section>
        """,
    }

    rendered_sections = "\n".join(
        sections[key] for key in order if sections.get(key)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(seo_title)}</title>
<meta name="description" content="{escape(meta_description)}">
<meta name="robots" content="noindex,follow">
<meta property="og:title" content="{escape(seo_title)}">
<meta property="og:description" content="{escape(meta_description)}">
<script type="application/ld+json">
{json.dumps({
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": str(name),
    "telephone": str(phone) if phone else None,
    "address": {
        "@type": "PostalAddress",
        "streetAddress": str(address) if address else None,
    } if address else None,
    "url": str(website) if website else None,
}, ensure_ascii=False, separators=(",", ":"))}
</script>
<link rel="stylesheet" href="styles.css">
<style id="ai-design-overrides">{design_css}</style>
</head>
<body>
<header class="header">
    <div class="container nav">
        <a class="logo" href="#">{escape(str(name))}</a>
        <nav class="site-nav" id="site-menu">
            <a href="#services">Services</a>
            <a href="#about">About</a>
            <a href="#process">How It Works</a>
            <a href="#faq">FAQ</a>
            <a href="#contact">Contact</a>
        </nav>
        <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-menu">Menu</button>
        {phone_html}
    </div>
</header>
<main class="rendered-main">
{rendered_sections}
</main>
<footer class="footer">
    <div class="container footer-grid">
        <div>
            <strong>{escape(str(name))}</strong>
            {f'<p>{escape(str(address))}</p>' if address else ""}
        </div>
        <div>{phone_html}</div>
    </div>
</footer>
<script src="script.js"></script>
</body>
</html>
"""



def generate_website(handoff_path):
    handoff_path = Path(handoff_path)

    handoff = load_json(handoff_path)

    business_path = handoff_path.parent / "business.json"

    if not business_path.exists():
        raise RuntimeError("business.json not found.")

    business = load_json(business_path)

    niche = get_niche(business, handoff)

    copy = generate_copy(
        business,
        handoff,
    )

    output_dir = handoff_path.parent / "website"
    output_dir.mkdir(exist_ok=True)

    design = copy.get("design_spec", {})
    design_path = output_dir / "design_spec.json"

    design_path.write_text(
        json.dumps(
            design,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    design_css = build_design_css(design)
    final_css = CSS + design_css

    html = build_html(
        business,
        copy,
        niche,
        output_dir,
        handoff,
    )

    (output_dir / "index.html").write_text(
        html,
        encoding="utf-8",
    )

    (output_dir / "styles.css").write_text(
        final_css,
        encoding="utf-8",
    )

    (output_dir / "script.js").write_text(
        JS,
        encoding="utf-8",
    )

    (output_dir / "ELEMENTOR_REBUILD_NOTES.md").write_text(
        """# Elementor Rebuild Notes

Recreate the generated page using Elementor Pro.

Recommended structure:

- Header
- AI-selected page sections from `design_spec.section_order`
- Footer

Use `design_spec.reference_selection` and `design_spec.reference_analysis` as the design rationale.
Use `design_spec.composition` to guide each section's Elementor container/layout.

Recommended widgets:

- Containers
- Heading
- Text Editor
- Button
- Icon
- Icon Box
- Accordion
- Form
- Google Maps when appropriate

Do not add unsupported business claims.

Images are generated as local files in `images/` for the concept build.
""",
        encoding="utf-8",
    )

    print(
        f"[design] Direction: "
        f"{design.get('direction', 'Clean Professional')}"
    )

    print(
        f"[design] Layout: "
        f"{design.get('layout_style', 'Standard Elementor layout')}"
    )

    print(
        f"[design] Elementor notes: "
        f"{design.get('elementor_notes', [])}"
    )
    print(f"[design] Reference patterns: {design.get('reference_patterns', [])}")
    print(f"[design] Dark sections: {design.get('design_system', {}).get('dark_sections', [])}")
    print(f"[seo] Title: {copy.get('seo', {}).get('title', '')}")
    print(f"[seo] Primary keyword: {copy.get('seo', {}).get('primary_keyword', '')}")

    return output_dir


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Generate premium local-business "
            "landing pages using DeepSeek."
        )
    )

    parser.add_argument(
        "ai_handoff",
        help="Path to AI_HANDOFF.json",
    )

    args = parser.parse_args()

    result = generate_website(
        args.ai_handoff
    )

    print(
        f"\nWebsite created: {result}"
    )