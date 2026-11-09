#!/usr/bin/env python3
"""Compare Luminon annotation runs (v2 schema) with each other and with the abstract (v1).

  python scripts/compare_luminon_runs.py flash=outputs/pilot_v2/flash_v21.jsonl \
      haiku=outputs/pilot_v2/haiku_v21.jsonl pro=outputs/pilot_v2/pro_v21.jsonl \
      --audit outputs/pilot_v2/revisjon_pilot.csv

Agreement is reported per pair on the shared ids, for kategori, makro,
underkategori (only where kategori agrees), referent and litterær_funksjon.
Runs are also compared with the abstract labels (v1 kategori and its macro
class) via abstract_sample_id. --audit writes windows where the runs disagree
on makro, for human review.
"""

import argparse
import csv
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import luminon_schema_v2 as S  # noqa: E402

FIELDS = ["kategori", "makro", "underkategori", "referent", "litterær_funksjon"]
V1_FILES = [Path("outputs/luminon_annotations.jsonl"), Path("outputs/luminon_round2_annotations.jsonl")]


def kappa(a: list, b: list) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] / n * cb[k] / n for k in set(a) | set(b))
    return 1.0 if pe == 1 else round((po - pe) / (1 - pe), 3)


def load(path: Path) -> dict[str, dict]:
    rows = {}
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        if not r.get("errors"):
            rows[r["id"]] = r
    return rows


def load_v1() -> dict[str, dict]:
    v1 = {}
    for p in V1_FILES:
        if p.exists():
            for line in p.open(encoding="utf-8"):
                r = json.loads(line)
                m = S.macro_of(r["domain"], r["kategori"])
                v1[r["id"]] = {"kategori": r["kategori"], "makro": m,
                               "litterær_funksjon": S.old_funksjon_to_v2(r.get("litterær_funksjon", ""))}
    return v1


def agreement(ra: dict, rb: dict, field: str, ids: list[str]):
    if field == "underkategori":
        ids = [i for i in ids if ra[i]["kategori"] == rb[i]["kategori"] and S.subcategories(ra[i]["domain"], ra[i]["kategori"])]
    a = [ra[i].get(field) for i in ids]
    b = [rb[i].get(field) for i in ids]
    if not ids:
        return 0, None, None
    return len(ids), round(sum(x == y for x, y in zip(a, b)) / len(ids), 3), kappa(a, b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", metavar="NAME=PATH")
    ap.add_argument("--audit", type=Path)
    ap.add_argument("--json", type=Path, help="write all numbers as JSON")
    args = ap.parse_args()

    runs = {}
    for spec in args.runs:
        name, path = spec.split("=", 1)
        runs[name] = load(Path(path))
        print(f"{name}: {len(runs[name])} gyldige annoteringer")
    out = {"pairs": {}, "vs_abstract": {}, "distributions": {}}

    print("\n## Parvis enighet (andel / kappa)")
    for a, b in itertools.combinations(runs, 2):
        ids = sorted(set(runs[a]) & set(runs[b]))
        print(f"\n{a} vs {b} (n={len(ids)})")
        out["pairs"][f"{a}~{b}"] = {}
        for f in FIELDS:
            n, p, k = agreement(runs[a], runs[b], f, ids)
            out["pairs"][f"{a}~{b}"][f] = {"n": n, "agree": p, "kappa": k}
            print(f"  {f:20s} n={n:4d}  {p}  κ={k}")
        by_dom = defaultdict(list)
        for i in ids:
            by_dom[runs[a][i]["domain"]].append(i)
        for d, dids in sorted(by_dom.items()):
            n, p, k = agreement(runs[a], runs[b], "makro", dids)
            print(f"    makro {d:22s} n={n:4d}  {p}  κ={k}")

    v1 = load_v1()
    print("\n## Mot abstraktet (v1-etiketter via abstract_sample_id)")
    for name, rows in runs.items():
        ids = [i for i, r in rows.items() if r.get("abstract_sample_id") in v1]
        if not ids:
            continue
        old = {i: v1[rows[i]["abstract_sample_id"]] for i in ids}
        res = {}
        for f in ["kategori", "makro", "litterær_funksjon"]:
            a = [old[i][f] for i in ids]
            b = [rows[i].get(f) for i in ids]
            res[f] = {"n": len(ids), "agree": round(sum(x == y for x, y in zip(a, b)) / len(ids), 3), "kappa": kappa(a, b)}
        out["vs_abstract"][name] = res
        print(f"  {name:8s} n={len(ids):4d}  " + "  ".join(f"{f}: {v['agree']} (κ={v['kappa']})" for f, v in res.items()))

    print("\n## Fordeling av makroklasse per undergruppe")
    subs = sorted({r["subgroup"] for rows in runs.values() for r in rows.values()})
    for s in subs:
        line = []
        for name, rows in runs.items():
            c = Counter(r["makro"] for r in rows.values() if r["subgroup"] == s)
            n = sum(c.values())
            if n:
                line.append(f"{name}: " + " ".join(f"{m[:4]}={100 * c[m] / n:.0f}%" for m in S.MACRO))
                out["distributions"].setdefault(s, {})[name] = {m: c[m] for m in S.MACRO}
        print(f"  {s:22s} " + " | ".join(line))

    if args.audit:
        names = list(runs)
        ids = sorted(set.intersection(*(set(runs[n]) for n in names)))
        with args.audit.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "domene", "undergruppe", "år", "vindu"]
                       + [f"{n}_{x}" for n in names for x in ("kategori", "underkategori", "makro", "begrunnelse")]
                       + ["vurdering", "kommentar"])
            n_out = 0
            for i in ids:
                if len({runs[n][i]["makro"] for n in names}) > 1:
                    r0 = runs[names[0]][i]
                    w.writerow([i, r0["domain"], r0["subgroup"], r0["year"], r0["concordance"]]
                               + [runs[n][i].get(x) for n in names for x in ("kategori", "underkategori", "makro", "begrunnelse")]
                               + ["", ""])
                    n_out += 1
        print(f"\n{n_out} vinduer med uenighet om makroklasse skrevet til {args.audit}")
    if args.json:
        args.json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
