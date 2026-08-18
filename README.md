# Cessna

Daily aggregator of **classic Cessna taildragger** classified listings from
[Barnstormers.com](https://www.barnstormers.com), published as a static page
(`docs/index.html`) meant to be embedded via `<iframe>` on taildraggers.com.

Cessna makes dozens of models (152, 172, 182, 206, jets, ...), so this scraper
pulls from broad Cessna/taildragger category pages and then keeps only ads
whose title matches one of a specific allowlist of models — see
[Model filter](#model-filter) below. Everything else (172s, 182s, off-brand
listings that leak into a category page, etc.) is discarded before it's even
fetched.

Controller.com was evaluated (in the companion [Aeronca](https://github.com/taildraggers/aeronca)
repo) and dropped: its search results are only reachable through an internal
client-side widget (not a plain URL), which a headless browser can't drive
reliably for an unattended daily job.

## Model filter

Only listings whose title contains one of these (case/hyphen/space-insensitive)
are published:

- Cessna 120
- Cessna 140
- Cessna 170
- Cessna 180
- Cessna 190
- Cessna 195
- L-19
- Skywagon
- Ag Wagon
- Cessna Taildragger

Edit `TARGET_MODEL_PHRASES` in `scraper/barnstormers.py` to change this list.
Matching also accounts for how sellers actually write these titles: abbreviated
forms like "C180" instead of "Cessna 180" (common on parts listings), and
modifier words between the make and model, like "Cessna Turbo 195A For Sale".

## How it works

- `scraper/barnstormers.py` searches Barnstormers.com's Cessna category and the
  general Antique-Classic/Taildragger category, follows pagination, then
  filters the resulting listing URLs against the model allowlist above
  (Barnstormers builds each listing's URL slug directly from the ad's own
  title, so this filter runs before any detail page is fetched). Only the
  matching listings get their detail page visited to pull out price, location,
  and posted date (falling back to regex heuristics over the visible text
  since the site doesn't expose structured data); the title itself is derived
  from the listing URL's own SEO slug, since every detail page shares one
  generic `<title>`/`<h1>`. The final parsed title is checked against the
  model allowlist again as a safety net.
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
- The model filter assumes a listing's title is accurately reflected in its
  URL slug, which has held true for every Barnstormers listing seen so far
  across this and the companion Aeronca/American Champion/Aviat repos, with
  one caveat: Barnstormers truncates very long slugs (seen cutting "...Sport
  Taildragger" down to "...Sport-Taildrag"), so a small number of ads whose
  matching phrase falls right at the truncation point could be missed.
