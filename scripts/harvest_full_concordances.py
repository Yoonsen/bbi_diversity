#!/usr/bin/env python3
"""Full (unsampled) concordance extraction for the DHNB 2027 lexicon.

Corpus: data/barn.csv, 2000-2024, langs == 'nob', fiction (Kristin's column
takes precedence over literaryform). Same 34 subgroups and same strict
token matching as the abstract harvest, but every hit is kept.

Outputs (outputs/full_fiction/):
  concordances_full.jsonl   one row per (subgroup, book, window)
  book_word_freq.csv        token counts per book x word form (from /frequencies)
  harvest_full_summary.json per-subgroup counts and completeness check
"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lexicon_dhnb2027 import LEXICON, surface_forms  # noqa: E402

API = "https://api.nb.no/dhlab"
BOLD_RE = re.compile(r"<b>(.*?)</b>", flags=re.IGNORECASE)
URN_BATCH = 150
CONC_LIMIT = 20000


def post(endpoint: str, payload: dict, timeout: int = 300):
    req = urllib.request.Request(
        f"{API}/{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            print(f"  retry {endpoint} ({e})", file=sys.stderr)
            time.sleep(2 * (attempt + 1))


def load_corpus(path: Path, y0: int, y1: int) -> dict[str, dict]:
    books = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                year = int(float(row["year"]))
            except (TypeError, ValueError):
                continue
            form = (row.get("kristin") or "").strip() or row.get("literaryform", "")
            if not (y0 <= year <= y1 and "Skjønn" in form and row.get("langs", "").strip() == "nob"):
                continue
            urn = row["urn"].strip()
            books[urn] = {
                "urn": urn,
                "dhlabid": (row.get("dhlabid") or "").split(".")[0],
                "year": year,
                "title": row.get("title", ""),
                "authors": row.get("authors", ""),
            }
    return books


def load_previous_ids(paths: list[Path]) -> dict[tuple[str, str], str]:
    """Map (urn, concordance) -> id from the sampled abstract harvest."""
    prev = {}
    for p in paths:
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                prev[(r["urn"], r["concordance"])] = r["id"]
    return prev


def harvest_subgroup(domain, subgroup, words, urns, books, did2urn):
    valid = {w.lower() for w in words}
    query = " OR ".join(f for w in words for f in surface_forms(w))
    rows, seen = [], set()
    batches = [urns[i:i + URN_BATCH] for i in range(0, len(urns), URN_BATCH)]
    while batches:
        batch = batches.pop()
        data = post("conc", {"urns": batch, "query": query, "window": 25, "limit": CONC_LIMIT})
        if not isinstance(data, dict) or "conc" not in data:
            raise RuntimeError(f"{subgroup}: unexpected response {str(data)[:200]}")
        if len(data["conc"]) >= CONC_LIMIT:
            if len(batch) == 1:
                raise RuntimeError(f"{subgroup}: single book {batch[0]} exceeds limit")
            mid = len(batch) // 2
            batches += [batch[:mid], batch[mid:]]
            continue
        for k, conc in data["conc"].items():
            ident = str(data["urn"][k])
            urn = ident if ident in books else did2urn.get(ident)
            if not urn:
                continue
            targets = [t.strip() for t in BOLD_RE.findall(conc) if t.strip().lower() in valid]
            if not targets or (urn, conc) in seen:
                continue
            seen.add((urn, conc))
            b = books[urn]
            rows.append({
                "domain": domain,
                "subgroup": subgroup,
                "urn": urn,
                "dhlabid": b["dhlabid"],
                "year": b["year"],
                "title": b["title"],
                "authors": b["authors"],
                "matched_word": targets[0].lower(),
                "target_token": targets[0],
                "n_targets_in_window": len(targets),
                "concordance": conc,
            })
    rows.sort(key=lambda r: (r["year"], r["urn"], r["concordance"]))
    return subgroup, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default="data/barn.csv", type=Path)
    ap.add_argument("--out", default="outputs/full_fiction", type=Path)
    ap.add_argument("--from-year", type=int, default=2000)
    ap.add_argument("--to-year", type=int, default=2024)
    ap.add_argument("--only", nargs="*", help="restrict to these subgroups")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    books = load_corpus(args.corpus, args.from_year, args.to_year)
    did2urn = {b["dhlabid"]: u for u, b in books.items() if b["dhlabid"]}
    print(f"Corpus: {len(books)} non-translated Bokmål fiction books {args.from_year}-{args.to_year}")

    lexicon = [t for t in LEXICON if not args.only or t[1] in args.only]
    form2group = {}
    for _, sub, words in lexicon:
        for w in words:
            for f in surface_forms(w):
                form2group.setdefault(f, set()).add(sub)
    forms = sorted(form2group)

    # 1. Token counts per book and word form (also the TF/DF basis for burstiness).
    print(f"Fetching frequencies for {len(forms)} word forms ...")
    urn_list = sorted(books)
    freq_rows = []
    for i in range(0, len(forms), 60):
        freq_rows += post("frequencies", {"urns": urn_list, "words": forms[i:i + 60], "cutoff": 0})
    book_freq = []  # (urn, form, count, doc_tokens)
    group_urns = defaultdict(set)
    group_tokens = Counter()
    for r in freq_rows:
        if not isinstance(r, list) or len(r) < 3 or int(r[2]) <= 0:
            continue
        ident = str(r[0])
        urn = ident if ident in books else did2urn.get(ident)
        if not urn or r[1] not in form2group:
            continue
        book_freq.append((urn, r[1], int(r[2]), r[3] if len(r) > 3 else ""))
        for sub in form2group[r[1]]:
            group_urns[sub].add(urn)
            group_tokens[sub] += int(r[2])

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "book_word_freq.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["urn", "dhlabid", "year", "word_form", "count", "doc_tokens"])
        for urn, form, cnt, tok in sorted(book_freq):
            w.writerow([urn, books[urn]["dhlabid"], books[urn]["year"], form, cnt, tok])

    # 2. Full concordances per subgroup.
    prev = load_previous_ids([Path("outputs/concordances_for_luminon.jsonl"),
                              Path("outputs/concordances_round2.jsonl")])
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(harvest_subgroup, d, s, ws, sorted(group_urns[s]), books, did2urn)
                for d, s, ws in lexicon if group_urns[s]]
        for fut in futs:
            sub, rows = fut.result()
            results[sub] = rows
            print(f"[{sub}] {len(rows)} windows in {len({r['urn'] for r in rows})} books "
                  f"(frequencies: {group_tokens[sub]} tokens in {len(group_urns[sub])} books)")

    summary, n_total, n_prev = {}, 0, 0
    with (args.out / "concordances_full.jsonl").open("w", encoding="utf-8") as f:
        for dom, sub, _ in lexicon:
            rows = results.get(sub, [])
            for i, r in enumerate(rows):
                r["id"] = f"{sub}_full_{i:05d}"
                r["abstract_sample_id"] = prev.get((r["urn"], r["concordance"]))
                n_prev += r["abstract_sample_id"] is not None
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_total += len(rows)
            tokens_in_conc = sum(r["n_targets_in_window"] for r in rows)
            summary[sub] = {
                "domain": dom,
                "windows": len(rows),
                "books_with_windows": len({r["urn"] for r in rows}),
                "freq_tokens": group_tokens[sub],
                "freq_books": len(group_urns[sub]),
                "target_tokens_in_windows": tokens_in_conc,
                "coverage_books": round(len({r["urn"] for r in rows}) / max(1, len(group_urns[sub])), 3),
                "in_abstract_sample": sum(1 for r in rows if r["abstract_sample_id"]),
                "windows_by_period": dict(sorted(Counter(f"{r['year'] // 5 * 5}-{r['year'] // 5 * 5 + 4}" for r in rows).items())),
            }
    summary["_meta"] = {
        "corpus_books": len(books),
        "years": [args.from_year, args.to_year],
        "window": 25,
        "total_windows": n_total,
        "linked_to_abstract_sample": n_prev,
    }
    (args.out / "harvest_full_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {n_total} windows ({n_prev} already in the abstract sample) to {args.out}")


if __name__ == "__main__":
    main()
