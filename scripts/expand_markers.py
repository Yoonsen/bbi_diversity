#!/usr/bin/env python3
"""Find candidate markers for a domain, with the four routes from doc-to-vec.

Stage 1 (fetch): chunk postings (~250-word blocks, bag of words) from
/dhlab/chunks for seed books (first editions with >= 1 lived window in the
domain, Luminon run) and an equally large random reference sample.

Stage 2 (score): for every word in those books
  1. chunk_ppmi   – over-representation in chunks that contain a seed marker
                    (seed books only) relative to all chunks
  2. book_z       – log-odds z of document frequency, seed books vs reference
                    books (the "bærende ramme" / frame route)
  3. fano_med     – median within-book Fano factor in seed books (burstiness;
                    > 1 means the word clusters in passages)
  4. galakse      – community in the chunk co-occurrence graph of the top
                    candidates plus the seed markers (Louvain)
  plus kontekst_z – log-odds z of the model's context lemmas, lived vs other
                    windows (matches word forms only when they are lemmas)

  python scripts/expand_markers.py fetch --domains funksjon flerkulturell --out outputs/markers
  python scripts/expand_markers.py score --domains funksjon flerkulturell --out outputs/markers

The chunk files are word counts per block (no running text). They are working
data for internal research and are not to be published.
"""

import argparse
import csv
import json
import math
import random
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest_full_concordances import first_editions, load_corpus  # noqa: E402
from lexicon_dhnb2027 import LEXICON, surface_forms  # noqa: E402

API = "https://api.nb.no/dhlab"
# Majority baselines and homonym tests are not seeds for minority markers.
NOT_SEED = {"kirke_bygg", "bedehus_bygg", "kristendom_identitet", "jodedom_tora_test", "hetero_cis", "streit_ord"}
STOP = set("""og i på av en et til med for er ikke som om så men at her der da nå også bare litt mye mer helt veldig
alltid aldri hva hvem hvor jeg du han hun vi de den det seg meg deg oss dem var har hadde skal skulle vil ville kan
kunne må måtte blir ble være vært fra over under etter før inn ut opp ned noe noen alle andre sin sitt sine min mitt
mine din ditt dine hans hennes deres vår vårt våre hvis når fordi mens enn eller selv dette disse""".split())


def seeds_and_books(args, domain):
    books, _ = first_editions(load_corpus(args.corpus, 2000, 2024))
    subs = [s for d, s, _ in LEXICON if d == domain and s not in NOT_SEED]
    forms = {f for d, s, ws in LEXICON if s in subs for w in ws for f in surface_forms(w)}
    lived = set()
    for line in args.main.open(encoding="utf-8"):
        r = json.loads(line)
        if r["domain"] == domain and r["subgroup"] in subs and r.get("makro") == "lived" and r["urn"] in books:
            lived.add(r["urn"])
    rest = sorted(set(books) - lived)
    rng = random.Random(2027)
    ref = set(rng.sample(rest, min(len(lived), len(rest), args.max_ref)))
    return books, subs, {f.lower() for f in forms}, lived, ref


def fetch_chunks(urn, chunk_size=250):
    q = urllib.parse.urlencode({"urn": urn, "chunk_size": chunk_size})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"{API}/chunks?{q}", timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else []
        except Exception:  # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    return None


def cmd_fetch(args):
    out = args.out / "chunks"
    out.mkdir(parents=True, exist_ok=True)
    want = set()
    for d in args.domains:
        _, _, _, lived, ref = seeds_and_books(args, d)
        want |= lived | ref
        print(f"{d}: {len(lived)} bøker med levd treff, {len(ref)} referansebøker")
    todo = sorted(u for u in want if not (out / f"{u.replace(':', '_')}.json").exists())
    print(f"Henter blokker for {len(todo)} av {len(want)} bøker")
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_chunks, u): u for u in todo}
        for n, fut in enumerate(as_completed(futs), 1):
            u, chunks = futs[fut], fut.result()
            if chunks is None:
                failed += 1
                continue
            # keep lowercase alphabetic words only, counts per chunk
            slim = []
            for ch in chunks:
                c = Counter()
                for w, k in (ch or {}).items():
                    wl = str(w).lower()
                    if wl.isalpha():
                        c[wl] += int(k)
                slim.append(dict(c))
            (out / f"{u.replace(':', '_')}.json").write_text(json.dumps(slim, ensure_ascii=False), encoding="utf-8")
            if n % 200 == 0:
                print(f"  {n}/{len(todo)} (feilet {failed})", flush=True)
    print(f"Ferdig, {failed} bøker feilet")


def log_odds_z(a, na, b, nb, prior=0.5):
    la = math.log((a + prior) / (na - a + prior))
    lb = math.log((b + prior) / (nb - b + prior))
    return (la - lb) / math.sqrt(1 / (a + prior) + 1 / (b + prior))


def louvain(words, chunks, seed_forms, max_nodes):
    import networkx as nx
    from networkx.algorithms.community import louvain_communities
    idx = set(words[:max_nodes]) | seed_forms
    pair = Counter()
    single = Counter()
    for ch in chunks:
        present = sorted(w for w in ch if w in idx)
        for w in present:
            single[w] += 1
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                pair[(present[i], present[j])] += 1
    n = len(chunks)
    G = nx.Graph()
    for (a, b), c in pair.items():
        if c >= 5:
            pmi = math.log2(c * n / (single[a] * single[b]))
            if pmi > 0:
                G.add_edge(a, b, weight=pmi)
    if G.number_of_edges() == 0:
        return {}
    comms = louvain_communities(G, weight="weight", seed=2027, resolution=1.0)
    return {w: i for i, c in enumerate(sorted(comms, key=len, reverse=True)) for w in c}


def cmd_score(args):
    for d in args.domains:
        books, subs, seed_forms, lived, ref = seeds_and_books(args, d)
        seed_chunks, all_chunks, fano = [], [], defaultdict(list)
        df_lived, df_ref = Counter(), Counter()
        n_lived = n_ref = 0
        for u in sorted(lived | ref):
            p = args.out / "chunks" / f"{u.replace(':', '_')}.json"
            if not p.exists():
                continue
            chunks = json.loads(p.read_text(encoding="utf-8"))
            if not chunks:
                continue
            sets = [set(c) for c in chunks]
            all_chunks.extend(sets)
            vocab = set().union(*sets)
            if u in lived:
                n_lived += 1
                df_lived.update(vocab)
                seed_chunks.extend(s for s in sets if s & seed_forms)
                K = len(chunks)
                tot = Counter()
                sq = Counter()
                for c in chunks:
                    for w, k in c.items():
                        tot[w] += k
                        sq[w] += k * k
                for w, t in tot.items():
                    if t >= 3:
                        mu = t / K
                        fano[w].append((sq[w] / K - mu * mu) / mu)
            else:
                n_ref += 1
                df_ref.update(vocab)
        if not seed_chunks:
            print(f"{d}: ingen blokker funnet – kjør fetch først")
            continue
        a_cnt = Counter(w for s in seed_chunks for w in s)
        b_cnt = Counter(w for s in all_chunks for w in s)
        NS, NA = len(seed_chunks), len(all_chunks)

        # context lemmas from the model (lived vs other windows)
        L, O = Counter(), Counter()
        for line in args.main.open(encoding="utf-8"):
            r = json.loads(line)
            if r["domain"] == d and r["subgroup"] in subs and r["urn"] in books:
                for w in r.get("kontekstord_lemma") or []:
                    (L if r.get("makro") == "lived" else O)[w] += 1
        nl, no = sum(L.values()) or 1, sum(O.values()) or 1

        rows = []
        for w, a in a_cnt.items():
            if a < args.min_chunks or w in STOP or w in seed_forms or len(w) < 3:
                continue
            if df_lived[w] < max(args.min_books, 0.01 * n_lived):  # one series or author is not a marker
                continue
            if b_cnt[w] / NA > args.max_chunk_share:  # too common to be a marker
                continue
            rows.append({
                "ord": w,
                "blokker_med_markør": a,
                "chunk_ppmi": round(math.log2((a / NS) / (b_cnt[w] / NA)), 3),
                "bøker_levd": df_lived[w], "bøker_ref": df_ref[w],
                "book_z": round(log_odds_z(df_lived[w], n_lived, df_ref[w], n_ref), 2),
                "fano_med": round(sorted(fano[w])[len(fano[w]) // 2], 2) if fano[w] else "",
                "kontekst_z": round(log_odds_z(L[w], nl, O[w], no), 2) if L[w] + O[w] >= 5 else "",
            })
        # rank by chunk association weighted by how many seed books carry the word
        rows.sort(key=lambda r: (r["chunk_ppmi"] > 0, r["chunk_ppmi"] * math.log1p(r["bøker_levd"])), reverse=True)
        gal = louvain([r["ord"] for r in rows], seed_chunks, seed_forms, args.graph_nodes)
        seed_gal = Counter(gal[f] for f in seed_forms if f in gal)
        for r in rows:
            r["galakse"] = gal.get(r["ord"], "")
            r["galakse_har_markører"] = seed_gal.get(gal.get(r["ord"]), 0)
        out = args.out / f"kandidater_{d}.csv"
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        gals = defaultdict(list)
        for r in rows[: args.graph_nodes]:
            if r["galakse"] != "":
                gals[r["galakse"]].append(r["ord"])
        print(f"\n{d}: {n_lived} bøker med levd treff, {n_ref} referanser, {NS} markørblokker av {NA}. Skrev {out}")
        print("  topp 40 (chunk_ppmi):", ", ".join(r["ord"] for r in rows[:40]))
        for g, ws in sorted(gals.items(), key=lambda x: -seed_gal.get(x[0], 0))[:6]:
            members = [f for f in seed_forms if gal.get(f) == g]
            print(f"  galakse {g} (markører: {', '.join(sorted(members)[:6]) or '–'}): {', '.join(ws[:18])}")


def cmd_pilot(args):
    """Harvest all windows for each candidate, then annotate up to --per-candidate with the main model."""
    import subprocess
    spec = json.loads(args.candidates.read_text(encoding="utf-8"))["kandidater"]
    spec = [c for c in spec if c["domene"] in args.domains]
    lex = [[c["domene"], "kand_" + c["ord"][0], c["ord"]] for c in spec]
    args.out.mkdir(parents=True, exist_ok=True)
    lex_path = args.out / "kandidat_leksikon.json"
    lex_path.write_text(json.dumps(lex, ensure_ascii=False, indent=1), encoding="utf-8")
    here = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(here / "harvest_full_concordances.py"), "--lexicon", str(lex_path),
                    "--out", str(args.out / "conc")], check=True)
    sample = [f"{sub}={args.per_candidate}" for _, sub, _ in lex]
    subprocess.run([sys.executable, str(here / "run_luminon_v2.py"), "--input", str(args.out / "conc" / "concordances_full.jsonl"),
                    "--model", args.model, "--effort", args.effort, "--workers", "6", "--sample", *sample,
                    "--out", str(args.out / f"annotert_{args.model}.jsonl")], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["fetch", "score", "pilot"])
    ap.add_argument("--candidates", type=Path, default=Path("data/kandidatmarkorer_pilot.json"))
    ap.add_argument("--per-candidate", type=int, default=60)
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--main", type=Path, default=Path("outputs/full_v22/haikumed.jsonl"))
    ap.add_argument("--corpus", type=Path, default=Path("data/barn.csv"))
    ap.add_argument("--out", type=Path, default=Path("outputs/markers"))
    ap.add_argument("--max-ref", type=int, default=800)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--min-chunks", type=int, default=10)
    ap.add_argument("--min-books", type=int, default=10, help="minimum seed books containing the word")
    ap.add_argument("--max-chunk-share", type=float, default=0.05)
    ap.add_argument("--graph-nodes", type=int, default=200)
    args = ap.parse_args()
    {"fetch": cmd_fetch, "score": cmd_score, "pilot": cmd_pilot}[args.stage](args)


if __name__ == "__main__":
    main()
