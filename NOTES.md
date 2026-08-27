# NOTES - renewals total

## Why there is no official total here

The brief asks for PKR renewals due from **2026-08-03** to **2026-09-02** (assessment "today" = 2026-08-03).

The supplied 34-record `renewals_raw.csv` was never included in the assessment materials. TechAbout confirmed that in writing and told candidates not to invent the dataset or invent the total.

This repo only has a small `SYN-*` fixture under `data/raw/` so `clean.py` can be demonstrated. That means the official assessment total is **not available** from this submission.

When you run `python clean.py renewals_raw.csv` on the SYN-* file, stdout prints a payable-window sum for that demo data and labels it as synthetic. That printed number is **not** the TechAbout answer.

## How to get the total from the real file

1. Save the official CSV as `data/raw/renewals_raw.csv` (or pass its path to `clean.py`)
2. Run `python clean.py renewals_raw.csv`
3. Use the payable-window line from the summary, or sum `amount_pkr` in `data/processed/clean.csv` with:

```text
status == "active"
AND amount_pkr > 0
AND renews_on >= 2026-08-03
AND renews_on <= 2026-09-02
```

Both ends of the window are inclusive.

### Include in the total

- status is `active`
- `amount_pkr` is positive
- `renews_on` falls inside 2026-08-03 .. 2026-09-02

### Exclude from the total

- `cancelled` / `suspended` (these stay in `clean.csv`, but not in the payable sum)
- refunds / negative amounts (kept in `clean.csv` as negatives)
- USD rows (dropped during cleaning; no FX rate was given)
- ambiguous or impossible dates (dropped)
- conflicting duplicates (whole group dropped)
- anything else dropped while cleaning (missing customer, blank amount, bad domain, etc.)

## Cleaner judgement calls

**Ambiguous slash dates**  
If day and month are both ≤ 12 and DD/MM ≠ MM/DD, drop the row and log it in `issues.csv`. I do not guess.

Clear cases:
- `25/12/2025` → DD/MM
- `12/25/2025` → MM/DD
- `2025-11-30` → ISO as written
- `05/05/2025` → OK (same date either way)

**Duplicates**  
Identity = `customer_id` + `domain` + `service` + `renews_on`  
- same amount → keep the first row, log the merge  
- different amounts → drop all of them, log the conflict

**USD**  
Dropped. Converting without a rate would invent data.

**Refunds**  
Stored as negative `amount_pkr` in `clean.csv`, flagged in `issues.csv`, left out of the payable total.

**Cancelled / suspended**  
Kept in `clean.csv` with normalised status, flagged, left out of the payable total.
