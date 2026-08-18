# Cessna

Daily aggregator of **classic Cessna taildragger** classified listings from
[Barnstormers.com](https://www.barnstormers.com), published as a static page
(`docs/index.html`) meant to be embedded via `<iframe>` on taildraggers.com.

Controller.com was evaluated (in the companion [Aeronca](https://github.com/taildraggers/aeronca)
repo) and dropped: its search results are only reachable through an internal
client-side widget (not a plain URL), which a headless browser can't drive
reliably for an unattended daily job.

## Categories scraped

This pulls directly from six model-specific Barnstormers category pages
(each a dedicated model page, not a broad manufacturer hub):

- [C-120 Taildragger](https://www.barnstormers.com/category-17372-Cessna--C-120-Taildragger.html)
- [C-140 Taildragger](https://www.barnstormers.com/category-17373-Cessna--C-140-Taildragger.html)
- [C-170 Taildragger](https://www.barnstormers.com/category-17384-Cessna--C-170-Taildragger.html)
- [C-180 Skywagon](https://www.barnstormers.com/category-17396-Cessna--C-180-Skywagon.html)
- [C-185](https://www.barnstormers.com/category-17400-Cessna--C-185.html)
- [C-195](https://www.barnstormers.com/category-17404-Cessna--C-195.html)

Edit `CATEGORY_URLS` in `scraper/barnstormers.py` to change this list.

These are dedicated model categories rather than a broad hub, so most of
what's on them is published as-is — no requirement that a title mention
"Cessna" or a model number (that would also drop plenty of genuine, unbranded
parts listings like "185 Horizontal Stab"). Testing did turn up a handful of
off-brand listings leaking into these pages regardless (a Bellanca Decathlon,
a Piper Vagabond, a Helio Courier, even a car-trade ad), so
`scraper/barnstormers.py` drops any title that names a different aircraft
manufacturer or an unrelated item (`OFF_BRAND_PHRASES`), while keeping
everything else. (The earlier approach scraped Cessna's general category plus
a multi-brand taildragger category and filtered by an allowlist; it turned
out those broad pages returned mostly irrelevant 172/182/206 listings even
after filtering, which is why this now points at the specific categories
instead.)

## How it works

- `scraper/barnstormers.py` fetches each of the six category pages above,
  follows pagination, and visits every listing's detail page to pull out the
  price, location, and posted date (falling back to regex heuristics over the
  visible text since the site doesn't expose structured data). The title is
  derived from the listing URL's own SEO slug, since every detail page shares
  one generic `<title>`/`<h1>`.
- On top of the off-brand filter above, only whole-aircraft-for-sale listings are
  kept. Each ad's title must match one of the six target model numbers
  (120/140/170/180/185/195, see `_extract_model` in `scraper/barnstormers.py`);
  titles that read as parts, accessories, services, or raffles are dropped. Every
  surviving listing's title is rewritten to a canonical **`YEAR Cessna MODEL`**
  form when the ad states a model year (e.g. `1949 Cessna 170A`), or just
  **`Cessna MODEL`** when it doesn't - a missing year isn't disqualifying, since
  plenty of genuine ads simply don't state one in the title - regardless of how
  the original ad was worded, so the page reads consistently.
- `main.py` runs the scraper, de-duplicates results, and renders them into
  `docs/index.html` titled **"Other Cessna Ads on the Web"**, with
  one row per listing: Title (linked to the original ad), Price, Location,
  Date Posted, and Site Posted On. Links use `rel="noopener noreferrer"` and
  the page sets a `no-referrer` meta policy, so Barnstormers never sees that
  the click came from taildraggers.com.
- `.github/workflows/daily-scrape.yml` runs the whole thing once a day (13:00 UTC),
  commits the regenerated `docs/index.html` if it changed, and can also be triggered
  manually from the Actions tab (`workflow_dispatch`).

## One-time setup: enable GitHub Pages

This repo publishes `docs/index.html` as a plain static file — GitHub Pages just needs
to be pointed at it once:

1. Go to **Settings → Pages** in this repository.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Branch: `main`, folder: `/docs`. Save.
4. GitHub will publish the page at `https://taildraggers.github.io/cessna/`
   (may take a minute or two the first time).

Also check **Settings → Actions → General**:
- **Actions permissions**: "Allow all actions and reusable workflows".
- **Workflow permissions**: "Read and write permissions" (needed so the daily
  job can commit the regenerated page back to the repo).

## Embedding on taildraggers.com

```html
<iframe
  src="https://taildraggers.github.io/cessna/"
  title="Other Cessna Ads on the Web"
  style="width: 100%; height: 800px; border: 0;"
  loading="lazy">
</iframe>
```

## Running locally

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
python main.py
```

This writes/overwrites `docs/index.html`.

## Notes

- If Barnstormers changes its markup or is briefly unreachable, the run logs will
  show a `[warn]`/`[error]` line pointing at what broke rather than failing silently.
- The scraper identifies itself with a browser-like `User-Agent` and adds a short
  delay between requests to be polite to the site.
