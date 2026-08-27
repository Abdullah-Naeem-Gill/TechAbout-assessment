# TechAbout Assessment - Python Developer

Part A: clean messy PKHosting renewals CSV
Part B: politely collect metadata from TECHi.com articles

Python 3.10+, free libraries only. No credentials.

## Important: missing renewals file

The brief refers to a supplied `renewals_raw.csv` with 34 records. That file was never provided (TechAbout confirmed this in writing and said not to invent one).

What I did instead:
- Built `clean.py` for the defect cases in the brief (ambiguous dates, USD, refunds, domains, dups, etc.)
- Put a small synthetic fixture at `data/raw/renewals_raw.csv` (record IDs start with `SYN-`) so the pipeline can be run and tested
- Did **not** invent 34 "official" rows
- Did **not** treat any total from the SYN-* file as the assessment answer

`NOTES.md` has the include/exclude rules for the payable window, and how to get the real total once the official file exists.

If you run `clean.py` on the SYN-* fixture, stdout will print a demo window sum and a note that it is not the TechAbout total. Ignore that number for scoring.

## Setup

```bash
python -m venv .venv
```

Windows: `.venv\Scripts\activate`  
macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

Deps: `requests`, `beautifulsoup4`, `pytest`

## How to run

```bash
python clean.py renewals_raw.csv
python techi_audit.py
pytest -q
```

Outputs land in:
- `data/processed/clean.csv`
- `data/processed/issues.csv`
- `data/processed/techi_articles.csv`

Bare `renewals_raw.csv` resolves to `data/raw/renewals_raw.csv`.

## Layout

```text
clean.py
techi_audit.py
renewal_cleaner/
techi_scraper/
data/raw/
data/processed/
tests/
NOTES.md
requirements.txt
```

## Part A rules (short)

**Dates:** If one side of a slash date is > 12, the other reading is used (DD/MM or MM/DD). If both sides are ≤ 12 and the two readings disagree, the row is dropped - no guessing. Impossible dates drop. ISO dates kept as written. Normalised dates are written as ISO in `clean.csv` and logged in `issues.csv`.

**Money:** Handles `PKR` / `Rs` / commas / parentheses-as-negative. USD lines are dropped (brief gives no FX rate). Refunds stay in `clean.csv` as negative `amount_pkr` and are left out of the payable total.

**Domains:** Lowercase host, strip scheme / path / leading `www.`, keep real subdomains (e.g. `blog.example.com`).

**Status:** `active` / `cancelled` / `suspended` / `unknown`. Cancelled and suspended stay in `clean.csv` but are excluded from the payable total.

**Duplicates:** Key = `customer_id` + `domain` + `service` + `renews_on`. Same amount → keep the first row. Conflicting amounts → drop the whole group.

Every drop, normalisation, merge, and flag is written to `issues.csv`. Stdout prints rows in / kept / dropped / flagged, counts by status, and the payable-window sum.

## Part B

Starts at TECHi `robots.txt`, follows sitemap links, then pulls up to 20 article pages. Article URLs are not hardcoded.

- robots.txt respected
- identifiable User-Agent
- 5 second pause between each article request (logged)
- disk cache under `.cache/techi/` (cache hits skip the network; article pacing still waits 5s)
- one bad page does not stop the run
- CSV is updated as articles are saved

## Tests

`pytest -q` - offline tests for date / money / domain parsing, the cleaner pipeline on the SYN-* fixture, and scraper helpers (no live network).

## TECHi findings

From the crawl that produced `data/processed/techi_articles.csv` (20 rows):

- Columns: `url`, `slug`, `title`, `category`, `author_handle`, `date_text`, `date_iso`
- Categories in this run: Markets & Equities (5), AI & Intelligence (4), Policy & Impact (4), Tech Breakthroughs (4), Research Tools & Guides (2), Crypto & DeFi (1)
- Authors repeat across posts: zoha (5), fatimah-misbah (5), saba (4), then omer-sheikh, qaiser, umair-aslam, layloma
- Handles stored without `@`; titles stored without a trailing `| TECHi`
- Visible dates look like `August 19, 2026 · 7:24 PM EDT`; `date_iso` is the normalised calendar day (e.g. `2026-08-19`)
- This run filled every field; the code still leaves a cell blank and continues if a page is missing metadata

## Limitations

- Official renewal total still cannot be calculated until TechAbout supplies the 34-row file (see `NOTES.md`)
- Relative article dates that use "months ago" / "years ago" approximate with 30 / 365 days
- With more time I would add harder property tests and broader sitemap edge-case coverage
