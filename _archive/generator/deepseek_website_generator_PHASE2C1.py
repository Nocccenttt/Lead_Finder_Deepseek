import argparse
import json
import os
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from openai import OpenAI

from api_usage_logger import log_usage


load_dotenv()

MODEL = "deepseek-chat"


INSPIRATION_REFERENCE_BRIEF = """
Use these curated references as DESIGN INSPIRATION ONLY. Do not copy layouts, branding,
copy, assets, or distinctive compositions.

Admire The Web:
- Agency category: https://admiretheweb.com/category/agency/
  Useful patterns observed: agency/studio presentation, strong visual hierarchy, polished
  portfolio-style presentation, varied navigation and hero treatments.
- Professional category: https://admiretheweb.com/category/professional/
  Useful patterns observed: clean professional layouts, restrained typography, strong
  whitespace, fixed/sticky navigation, clear information hierarchy.
- Example: Shift Capital: https://admiretheweb.com/inspiration/shift-capital/
  Tags include fixed header/navigation, overlap, parallax, slideshow, smooth scroll.
- Example: Cecilia Halling Howells:
  https://admiretheweb.com/inspiration/cecilia-halling-howells/
  Tags include natural/earth colors, fixed header, large footer, reveal.

Best Website Gallery:
- Example: Beagle: https://bestwebsite.gallery/sites/sotd/2015/04/19/beagle
  Style tags: background photos, minimalist, responsive, one pager, sticky navigation.
- Example: Zumtobel Group:
  https://bestwebsite.gallery/sites/sotd/2021/01/07/zumtobel-group
  Style tags: full width, typography, background photos, responsive, sticky navigation.
- Example: Norgram: https://bestwebsite.gallery/sites/sotd/2017/03/13/norgram
  Style tags: full width, typography, agency website, case studies, minimalist,
  bright, responsive, sticky navigation.
- Example: Build in Amsterdam:
  https://bestwebsite.gallery/sites/sotd/2018/09/04/build-in-amsterdam
  Style tags: full width, typography, agency website, background photos, case studies,
  responsive, sticky navigation.

Translate these observations into an ORIGINAL Elementor-compatible design appropriate
to the supplied business. The references are pattern libraries, not templates.
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
Do not design for Divi, Gutenberg, Bricks, Webflow, Wix, Shopify, React, Vue, or custom backend systems.

Return ONLY valid JSON with exactly this structure. Keep every text field concise so the complete JSON fits within the output limit:
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
    "reference_patterns": [],
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
- The SEO title should normally contain the primary niche/service and verified city/state when available.
- The meta description should be natural, useful, locally relevant, and not stuffed with keywords.
- Use semantic variations instead of repeating the same keyword.
- General industry information may make the page more substantial, but never attribute general information to the business.
- Do not claim that the business provides a service unless the source verifies it.
- If services are not verified, return an empty services array and use general/contextual wording elsewhere.
- Do not invent service areas, credentials, experience, reviews, ratings, certifications, licenses, guarantees, pricing, or business history.
- Write for humans first while naturally supporting local search relevance.

DESIGN RULES:
- Do not automatically use the same dark/gold design for every business.
- Choose a design direction appropriate to the business.
- Possible directions include Premium Dark, Clean Professional, Bold Local Business, Luxury Editorial,
  Modern Corporate, Minimal Conversion, and Experimental Editorial.
- Avoid repetitive card grids, excessive rounded cards, generic gradients, predictable hero layouts,
  excessive decorative elements, and designs that cannot realistically be rebuilt in Elementor.
- section_order should contain only the sections actually needed.
- elementor_notes should contain 3-5 concise implementation notes.
- Do not copy an existing website. Use the supplied design_inspiration as a pattern library and
  translate its useful traits into an original design appropriate to this business.
- Do not force every business into the same visual language. Select only reference patterns that fit
  the business, niche, local audience, and conversion goal.
- Favor a small number of coherent design traits over a collection of unrelated effects.
- Build one coherent design_system that the renderer can apply globally; do not choose colors independently
  for each section.
- design_system.palette must use valid 6-digit hex colors. Keep text/background contrast strong.
- surface should support normal content, surface_alt should support cards, dark should be reserved for
  intentional contrast sections, and on_primary must be readable on primary buttons.
- dark_sections may contain only section keys from section_order and should normally contain no more than 2.
- spacing should be one of compact, comfortable, or spacious; container should be focused or wide.
- motion should describe subtle CSS/IntersectionObserver motion only; avoid distracting effects.
- reference_patterns should list 2-4 concise traits selected from the supplied inspiration brief that materially
  influenced this design. Do not name a reference as the design itself and do not copy its composition.

CONTENT RULES:
- Write for the verified niche, not a hardcoded industry.
- Keep copy natural, useful, local, and conversion-focused.
- Use verified city/state/address when available.
- Benefits should describe general customer-facing value unless a company-specific benefit is verified.
- Process should remain general: Contact, Schedule/Plan, Service/Completion.
- FAQ answers must remain supported by the source or be clearly general educational questions.
- Never use unsupported superlatives such as best, #1, top-rated, cheapest, fastest, most trusted, or guaranteed.
- Do not mention AI, LeadFinder, Wolf Forge, prompts, or internal processes.

IMAGES:
- The generated site MUST use relevant realistic photography related to the business niche.
- Return exactly 2 short image search queries.
- Do not request logos, fake company branding, screenshots, or identifiable celebrities.
- image_alt must contain 2 concise descriptive alt texts matching the image queries.
- Prefer realistic photography over abstract graphics.

Before returning JSON, verify that seo, design_spec, all required design fields, and all content fields exist.
Return ONLY JSON.
"""

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


JS = r"""
document.documentElement.classList.add("js-enabled");

var menuButton = document.querySelector(".menu-toggle");
var siteMenu = document.querySelector(".site-nav");

if (menuButton && siteMenu) {
    menuButton.addEventListener("click", function () {
        var open = siteMenu.classList.toggle("is-open");
        menuButton.setAttribute("aria-expanded", open ? "true" : "false");
    });

    siteMenu.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            siteMenu.classList.remove("is-open");
            menuButton.setAttribute("aria-expanded", "false");
        });
    });
}

document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener("click", function () {
        var target = document.querySelector(link.getAttribute("href"));
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
});

var revealItems = document.querySelectorAll(
    ".rendered-main > section, .service-card, .benefit-card, .process-card, details, .cta-box"
);

revealItems.forEach(function (item, index) {
    item.classList.add("reveal");
    item.style.transitionDelay = Math.min(index * 45, 270) + "ms";
});

if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries, obs) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });
    revealItems.forEach(function (item) { observer.observe(item); });
} else {
    revealItems.forEach(function (item) { item.classList.add("is-visible"); });
}
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


def check_inspiration_sources():
    urls = [
        "https://admiretheweb.com/category/agency/",
        "https://admiretheweb.com/category/professional/",
        "https://bestwebsite.gallery/sites/sotd/2015/04/19/beagle",
        "https://bestwebsite.gallery/sites/sotd/2021/01/07/zumtobel-group",
        "https://bestwebsite.gallery/sites/sotd/2017/03/13/norgram",
    ]

    reachable = 0

    for url in urls:
        try:
            request = Request(
                url,
                headers={"User-Agent": "LeadFinder Design Research/1.0"},
            )
            with urlopen(request, timeout=8) as response:
                if 200 <= response.status < 400:
                    reachable += 1
        except Exception:
            continue

    print(
        f"[inspiration] Reference sources reachable: "
        f"{reachable}/{len(urls)}"
    )


def generate_copy(business, handoff):
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    source = json.dumps(
        {
            "business": business,
            "niche": get_niche(business, handoff),
            "ai_handoff": handoff,
            "design_inspiration": INSPIRATION_REFERENCE_BRIEF,
        },
        ensure_ascii=False,
        indent=2,
    )

    check_inspiration_sources()

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
        max_tokens=2300,
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
        raise RuntimeError(
            "DeepSeek did not return a valid design_spec."
        )

    required_design_fields = [
        "direction",
        "visual_style",
        "layout_style",
        "hero_style",
        "navigation_style",
        "color_direction",
        "design_system",
        "reference_patterns",
        "typography_style",
        "card_style",
        "button_style",
        "section_order",
        "image_strategy",
        "elementor_compatible",
        "elementor_notes",
    ]

    missing = [
        field
        for field in required_design_fields
        if field not in design
    ]

    if missing:
        raise RuntimeError(
            "DeepSeek returned an incomplete design_spec. "
            f"Missing: {', '.join(missing)}"
        )

    colors = design.get("color_direction")

    if not isinstance(colors, dict):
        raise RuntimeError(
            "DeepSeek returned an invalid color_direction."
        )

    required_colors = [
        "primary",
        "accent",
        "background",
        "text",
    ]

    missing_colors = [
        color
        for color in required_colors
        if not colors.get(color)
    ]

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

    dark_sections = system.get("dark_sections", [])
    if not isinstance(dark_sections, list):
        raise RuntimeError("DeepSeek returned an invalid dark_sections list.")

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
    print(f"[design] Elementor notes: {design.get('elementor_notes')}")

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
        if (len(value) == 7 and value.startswith("#") and
                all(char in "0123456789abcdefABCDEF" for char in value[1:])):
            return value
        return fallback

    background = safe_color(palette.get("background"), safe_color(colors.get("background"), "#f6f3ec"))
    surface = safe_color(palette.get("surface"), background)
    surface_alt = safe_color(palette.get("surface_alt"), "#ffffff")
    text = safe_color(palette.get("text"), safe_color(colors.get("text"), "#172019"))
    muted = safe_color(palette.get("muted"), "#667066")
    primary = safe_color(palette.get("primary"), safe_color(colors.get("primary"), "#214b35"))
    accent = safe_color(palette.get("accent"), safe_color(colors.get("accent"), "#b88a45"))
    dark = safe_color(palette.get("dark"), "#101c18")
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
    if spacing == "compact":
        section_space = "clamp(64px, 7vw, 92px)"
        intro_space = "clamp(58px, 6vw, 82px)"
    elif spacing == "spacious":
        section_space = "clamp(82px, 9vw, 138px)"
        intro_space = "clamp(72px, 8vw, 112px)"
    else:
        section_space = "clamp(72px, 8vw, 112px)"
        intro_space = "clamp(64px, 7vw, 96px)"

    container = str(system.get("container", "wide")).lower()
    max_width = "1240px" if container == "wide" else "1080px"
    radius = str(system.get("radius", "medium")).lower()
    radius_value = {"small": "8px", "large": "24px"}.get(radius, "16px")
    shadow = str(system.get("shadow", "soft")).lower()
    shadow_value = "none" if shadow in ("none", "flat") else "0 18px 50px rgba(20,30,24,.10)"

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
    --border: rgba(23,32,25,.13);
    --font-body: {body_font};
    --font-heading: {heading_font};
    --section-space: {section_space};
    --intro-space: {intro_space};
    --max: {max_width};
    --radius: {radius_value};
    --shadow: {shadow_value};
    --gold: var(--accent);
    --gold-light: var(--accent);
}}

body {{ font-family: var(--font-body); color: var(--text); background: var(--bg); }}
h1, h2, h3, h4, .logo, .button {{ font-family: var(--font-heading); }}
h1, h2, h3, h4 {{ color: var(--text); }}
.container {{ max-width: var(--max); }}
.header {{ background: var(--surface); border-color: var(--border); }}
nav a {{ color: var(--muted); }}
nav a:hover, nav a:focus {{ color: var(--text); }}
.button.primary {{ background: var(--primary); color: var(--on-primary); box-shadow: var(--shadow); }}
.button.secondary {{ border-color: var(--border); background: var(--surface-alt); color: var(--text); }}
.eyebrow, .service-number, .benefit-number, .process-card > span {{ color: var(--primary); }}
.rendered-main > .section, .local-section, .cta-section {{ background: var(--surface); color: var(--text); }}
.dark, .process-section {{ background: var(--surface); }}
.service-card, .benefit-card, .process-card, details, .location-box, .hero-panel {{ background: var(--surface-alt); border-color: var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }}
.service-card {{ min-height: 220px; transition: transform .35s ease, box-shadow .35s ease, border-color .35s ease; }}
.service-card:hover {{ transform: translateY(-6px); box-shadow: 0 24px 60px rgba(20,30,24,.14); border-color: var(--primary); }}
.service-card h3 {{ margin-top: 42px; }}
.service-card p, .process-card p, .section-heading p, .large-copy, .intro-copy, .local-copy, .image-feature-copy p, .cta-box p, details p, .footer p {{ color: var(--muted); }}
.process-section, .local-section, .cta-box {{ background: var(--surface); }}
.cta-box {{ border-color: var(--border); border-radius: calc(var(--radius) + 4px); box-shadow: var(--shadow); }}
.hero {{ background: var(--surface); color: var(--text); }}
.hero-copy {{ color: var(--muted); }}
.hero-photo, .image-feature img {{ border-color: var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }}
.hero-full-bleed {{ min-height: min(760px, 88vh); display: grid; align-items: center; background: var(--dark); }}
.hero-full-bleed .hero-background {{ position: absolute; inset: 0; }}
.hero-full-bleed .hero-background img {{ width: 100%; height: 100%; object-fit: cover; display: block; animation: heroZoom 12s ease-out both; }}
.hero-full-bleed .hero-overlay {{ position: absolute; inset: 0; background: linear-gradient(90deg, color-mix(in srgb, var(--dark) 78%, transparent), color-mix(in srgb, var(--dark) 28%, transparent)); }}
.hero-full-bleed .hero-content-overlay {{ position: relative; z-index: 1; text-align: center; max-width: 980px; margin-inline: auto; padding-block: 110px; }}
.hero-full-bleed .hero-content-overlay .hero-copy {{ margin: 24px auto 30px; max-width: 760px; }}
.hero-full-bleed .hero-content-overlay .actions {{ justify-content: center; }}
.hero-full-bleed .hero-content-overlay h1, .hero-full-bleed .hero-content-overlay .hero-copy, .hero-full-bleed .hero-content-overlay .location {{ color: #fff; }}
.hero-full-bleed .hero-content-overlay .eyebrow {{ color: var(--accent); }}
.tone-dark {{ background: var(--dark) !important; color: #fff !important; }}
.tone-dark h1, .tone-dark h2, .tone-dark h3, .tone-dark h4, .tone-dark .large-copy, .tone-dark .hero-copy {{ color: #fff; }}
.tone-dark .eyebrow, .tone-dark .service-number, .tone-dark .benefit-number, .tone-dark .process-card > span {{ color: var(--accent); }}
.tone-dark .service-card, .tone-dark .benefit-card, .tone-dark .process-card, .tone-dark details, .tone-dark .location-box {{ background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.16); box-shadow: none; }}
.tone-dark .service-card p, .tone-dark .benefit-card p, .tone-dark .process-card p, .tone-dark details p {{ color: rgba(255,255,255,.72); }}
.reveal {{ will-change: transform, opacity; }}
.js-enabled .reveal {{ opacity: 0; transform: translateY(22px); transition: opacity .7s ease, transform .7s ease; }}
.js-enabled .reveal.is-visible {{ opacity: 1; transform: none; }}
.image-feature img, .hero-photo img {{ transition: transform .8s ease; }}
.hero-photo:hover img, .image-feature:hover img {{ transform: scale(1.025); }}
.menu-toggle {{ display: none; border: 1px solid var(--border); background: var(--surface-alt); color: var(--text); border-radius: 8px; padding: 10px 13px; font: inherit; cursor: pointer; }}
@keyframes heroZoom {{ from {{ transform: scale(1.04); }} to {{ transform: scale(1); }} }}
@media (max-width: 850px) {{
    .menu-toggle {{ display: inline-flex; align-items: center; justify-content: center; }}
    .site-nav {{ display: none; position: absolute; left: 4%; right: 4%; top: calc(100% + 8px); padding: 14px; flex-direction: column; gap: 4px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }}
    .site-nav.is-open {{ display: flex; }}
    .site-nav a {{ padding: 11px 10px; }}
    .nav {{ position: relative; min-height: 68px; }}
    .hero-full-bleed {{ min-height: 680px; }}
    .hero-full-bleed .hero-content-overlay {{ padding-block: 90px; }}
}}
@media (prefers-reduced-motion: reduce) {{
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

    def tone_class(key, base):
        tone = "tone-dark" if key in dark_sections else "tone-light"
        return f"{base} {tone}"

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
                    <p class="large-copy">{escape(str(about))}</p>
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

1. Header
2. Hero
3. Intro
4. Services
5. About
6. Benefits
7. How It Works
8. Local Section
9. FAQ
10. CTA
11. Footer

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