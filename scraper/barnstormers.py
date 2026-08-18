"""Scraper for classic Cessna taildragger listings on barnstormers.com.

Cessna makes dozens of models (152, 172, 182, 206, jets, ...), so unlike the
single-manufacturer Aeronca/American Champion/Aviat scrapers, this one pulls
from broader Cessna/taildragger category pages and then keeps only listings
whose title matches one of the specific taildragger models requested:
Cessna 120/140/170/180/190/195, L-19, Skywagon, Ag Wagon, or "Cessna
Taildragger". Barnstormers builds each listing's URL slug directly from the
ad's own title, so the model filter runs against that slug before ever
fetching a detail page - this avoids downloading every unrelated 172/182/206
ad just to discard it.
"""
from __future__ import annotations

import re
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from .common import Listing, extract_date, extract_location, extract_price, fetch

SITE_NAME = "Barnstormers.com"
BASE = "https://www.barnstormers.com"

# Broad category pages likely to carry the target Cessna taildragger models.
CATEGORY_URLS = [
    f"{BASE}/category-17352-Cessna.html",
    f"{BASE}/category-16571-Antique-Classic--Taildragger.html",
]

# Only ads whose title matches one of these (case/hyphen/space-insensitive)
# are kept. Edit this list to change which models get published.
TARGET_MODEL_PHRASES = [
    "cessna 120",
    "cessna 140",
    "cessna 170",
    "cessna 180",
    "cessna 190",
    "cessna 195",
    "l 19",
    "skywagon",
    "ag wagon",
    "cessna taildragger",
]

MAX_PAGES = 10
LISTING_LINK_RE = re.compile(r"^/classified-(\d+)-(.+)\.html$")
GENERIC_SITE_TITLE_SNIPPET = "barnstormers.com find aircraft"


def _normalize(text: str) -> str:
    """Lowercase and collapse hyphens/whitespace so phrase matching is forgiving
    about "AG-Wagon" vs "Ag Wagon" vs "AGWAGON", "L-19" vs "L 19", etc."""
    text = text.lower()
    text = re.sub(r"[-_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _matches_target_models(title: str) -> bool:
    normalized = _normalize(title)
    return any(phrase in normalized for phrase in TARGET_MODEL_PHRASES)


def _title_from_url(url: str) -> str:
    """Listing pages share a generic <title>/<h1>, but the URL slug is the ad's own title."""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    match = LISTING_LINK_RE.match("/" + slug)
    if not match:
        return unquote(slug)
    return unquote(match.group(2)).replace("-", " ").strip()


def _find_listing_links(html: str) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("?")[0]
        if LISTING_LINK_RE.match(href):
            links.add(urljoin(BASE, href))
    return links


def _find_next_page_url(html: str, current_url: str) -> str | None:
    """Find a "next page" link on a category listing page, if any."""
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        rel = a.get("rel") or []
        if text in ("next", "next »", "»", "next page", ">") or "next" in rel:
            candidate = urljoin(current_url, a["href"])
            if candidate != current_url:
                return candidate
    return None


def _debug_dump_hrefs(html: str, limit: int = 25) -> None:
    soup = BeautifulSoup(html, "lxml")
    hrefs = [a["href"] for a in soup.find_all("a", href=True)]
    interesting = [h for h in hrefs if "classified" in h.lower() or "cessna" in h.lower()]
    sample = interesting[:limit] or hrefs[:limit]
    print(f"  [debug] {len(hrefs)} total <a href> on page; sample: {sample}")


def _parse_detail_page(url: str, html: str) -> Listing | None:
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    if title:
        title = re.sub(r"\s*[\|\-]\s*Barnstormers.*$", "", title, flags=re.IGNORECASE).strip()
    if not title or GENERIC_SITE_TITLE_SNIPPET in title.lower():
        title = _title_from_url(url)
    if not title:
        return None

    text = soup.get_text(" ", strip=True)
    price = extract_price(text)
    location = extract_location(text)
    date_posted = extract_date(text)

    return Listing(
        title=title,
        price=price,
        location=location,
        date_posted=date_posted,
        site=SITE_NAME,
        url=url,
    )


def scrape() -> list[Listing]:
    print(f"[{SITE_NAME}] starting scrape")
    all_links: set[str] = set()

    for category_url in CATEGORY_URLS:
        seen_this_category: set[str] = set()
        url = category_url
        for page in range(1, MAX_PAGES + 1):
            html = fetch(url)
            if not html:
                break
            links = _find_listing_links(html)
            new_links = links - seen_this_category
            print(f"  [{category_url}] page {page}: {len(links)} links ({len(new_links)} new)")
            if page == 1 and not links:
                _debug_dump_hrefs(html)
            seen_this_category |= links
            next_url = _find_next_page_url(html, url)
            if not next_url or not new_links:
                break
            url = next_url
        all_links |= seen_this_category

    print(f"[{SITE_NAME}] {len(all_links)} total listing URLs found across categories")

    candidate_links = {url for url in all_links if _matches_target_models(_title_from_url(url))}
    print(f"[{SITE_NAME}] {len(candidate_links)} match target Cessna taildragger models")

    listings: list[Listing] = []
    for url in sorted(candidate_links):
        html = fetch(url)
        if not html:
            continue
        listing = _parse_detail_page(url, html)
        # Belt-and-suspenders: re-check the final parsed title too, in case
        # the real page title differs from the URL-slug guess.
        if listing and _matches_target_models(listing.title):
            listings.append(listing)

    print(f"[{SITE_NAME}] parsed {len(listings)} listings")
    return listings
