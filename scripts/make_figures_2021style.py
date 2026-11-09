#!/usr/bin/env python3
"""Figures in the style of Ørjasæter & Johnsen (2021), raw counts vs Luminon-confirmed.

The 2021 report counted marker words per book (frequency, intensity, co-occurrence).
Here each figure shows that raw count next to what remains after Luminon
interpretation (windows whose macro class is `lived`).

  python scripts/make_figures_2021style.py --main outputs/full_v22/haikumed.jsonl --out outputs/figs_v22

Figures:
  fig1_boker_per_identitet.png   books with markers per 100 titles (2021 fig. 3)
  fig2_intensitet.png            hits per book where the identity occurs (2021 fig. 2/4)
  fig3_over_tid.png              book spread per five-year period, by domain
  fig4_samforekomst.png          identities that occur in the same books (2021 fig. 5, Jaccard instead of Louvain)
  fig5_intensitet_over_tid.png   b_w per five-year period, by domain
  tall_figurer.csv               all numbers behind fig. 1-3 (table view)
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest_full_concordances import first_editions, load_corpus  # noqa: E402
from lexicon_dhnb2027 import LEXICON, surface_forms  # noqa: E402

# Reference palette (dataviz skill): one hue, two ordinal steps, validated light.
RAW = "#86b6ef"      # blue 250 – raw count
LIVED = "#1c5cab"    # blue 550 – Luminon-confirmed
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SEQ = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
PERIODS = [(2000, 2004), (2005, 2009), (2010, 2014), (2015, 2019), (2020, 2024)]
DOMAIN_NO = {"religion": "Religion", "funksjon": "Funksjonsnedsettelse", "kjonn_seksualitet": "Kjønn og seksualitet",
             "nasjonale_minoriteter": "Samer og nasjonale minoriteter", "flerkulturell": "Flerkulturelt og migrasjon"}
# Fig. 3 follows the abstract: minority markers only; majority baselines and the homonym test are left out.
FIG3_EXCLUDE = {"kirke_bygg", "bedehus_bygg", "kristendom_identitet", "jodedom_tora_test", "hetero_cis", "streit_ord"}
LABEL = {s: s.replace("_", " ") for _, s, _ in LEXICON}

plt.rcParams.update({
    "font.family": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK, "axes.facecolor": SURF,
    "figure.facecolor": SURF, "savefig.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False,
})




def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main", type=Path, required=True)
    ap.add_argument("--freq", type=Path, default=Path("outputs/full_fiction/book_word_freq.csv"))
    ap.add_argument("--corpus", type=Path, default=Path("data/barn.csv"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--keep-editions", action="store_true",
                    help="keep later editions/reprints (default: only the first edition of each title+author)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    books = load_corpus(args.corpus, 2000, 2024)
    n_dropped = 0
    if not args.keep_editions:
        books, n_dropped = first_editions(books)
    N = len(books)
    year = {u: b["year"] for u, b in books.items()}
    n_period = Counter(next(p for p in PERIODS if p[0] <= b["year"] <= p[1]) for b in books.values())
    subs = [s for _, s, _ in LEXICON]
    dom = {s: d for d, s, _ in LEXICON}
    form2subs = defaultdict(set)
    for _, s, ws in LEXICON:
        for w in ws:
            for f in surface_forms(w):
                form2subs[f].add(s)

    # Raw: every token of a marker word counts (as in 2021).
    raw_tok = defaultdict(Counter)  # sub -> urn -> tokens
    with args.freq.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["urn"] not in books:
                continue
            for s in form2subs.get(r["word_form"], ()):
                raw_tok[s][r["urn"]] += int(r["count"])
    # Luminon: windows classed as lived.
    lived = defaultdict(Counter)    # sub -> urn -> lived windows
    for line in args.main.open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("makro") == "lived" and r["urn"] in books:
            lived[r["subgroup"]][r["urn"]] += 1

    rows = []
    for s in subs:
        df_r, tf_r = len(raw_tok[s]), sum(raw_tok[s].values())
        df_l, tf_l = len(lived[s]), sum(lived[s].values())
        rows.append({"domene": dom[s], "undergruppe": s, "bøker_rå": df_r, "bøker_levd": df_l,
                     "per100_rå": 100 * df_r / N, "per100_levd": 100 * df_l / N,
                     "bw_rå": tf_r / df_r if df_r else 0, "bw_levd": tf_l / df_l if df_l else 0,
                     "treff_rå": tf_r, "treff_levd": tf_l})

    # ---------- Fig 1 and 2: dumbbells grouped by domain ----------
    def dumbbell(key_raw, key_lived, xlabel, title, fname, fmt, exclude=()):
        use = [r for r in rows if r["undergruppe"] not in exclude]
        order = []
        for d in DOMAIN_NO:
            order.append(("head", d))
            order += [("row", r) for r in use if r["domene"] == d]
        fig, ax = plt.subplots(figsize=(7.2, 0.24 * len(order) + 1.2))
        y = 0
        yt, yl = [], []
        first = True
        widest = max(use, key=lambda r: abs(r[key_raw] - r[key_lived]))["undergruppe"]
        for kind, v in order:
            if kind == "head":
                yt.append(y); yl.append(DOMAIN_NO[v].upper())
                y += 1
                continue
            a, b = v[key_raw], v[key_lived]
            ax.plot([a, b], [y, y], color=GRID, lw=2, zorder=1, solid_capstyle="round")
            ax.scatter([a], [y], s=36, color=RAW, zorder=2, edgecolor=SURF, linewidth=1.5,
                       label="Rå ordtelling" if first else None)
            ax.scatter([b], [y], s=36, color=LIVED, zorder=3, edgecolor=SURF, linewidth=1.5,
                       label="Bekreftet levd (luminon)" if first else None)
            if v["undergruppe"] == widest:
                lo, hi = (a, b) if a < b else (b, a)
                ax.annotate("rå" if a > b else "levd", (hi, y), xytext=(7, 0), textcoords="offset points",
                            va="center", fontsize=8, color=INK2)
                ax.annotate("levd" if a > b else "rå", (lo, y), xytext=(0, 9), textcoords="offset points",
                            va="bottom", ha="center", fontsize=8, color=INK2)
            first = False
            yt.append(y); yl.append(LABEL[v["undergruppe"]])
            y += 1
        ax.set_yticks(yt, yl)
        for t, (kind, _) in zip(ax.get_yticklabels(), order):
            if kind == "head":
                t.set_fontweight("bold"); t.set_fontsize(8); t.set_color(INK2)
        ax.invert_yaxis()
        ax.set_xlim(left=0)
        ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel(xlabel)
        ax.set_title(title, loc="left", fontsize=11, color=INK, pad=22)
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(args.out / fname, dpi=200)
        plt.close(fig)

    dumbbell("per100_rå", "per100_levd", f"Bøker med treff per 100 titler (N = {N}, 2000–2024)",
             "Hvor mange bøker nevner identiteten – før og etter tolkning", "fig1_boker_per_identitet.png", "{:.1f}")
    dumbbell("bw_rå", "bw_levd", "Treff per bok der identiteten forekommer (b_w)",
             "Intensitet: hvor ofte identiteten nevnes når den først er der", "fig2_intensitet.png", "{:.1f}",
             exclude=("jodedom_tora_test",))  # raw b_w 28 (the name Tora) would flatten the rest

    # ---------- Fig 3: spread over time by domain ----------
    fig, axes = plt.subplots(1, 5, figsize=(12, 3.1), sharey=False)
    labels = [f"{a}–\n{b % 100:02d}" for a, b in PERIODS]
    trows = []
    for ax, d in zip(axes, DOMAIN_NO):
        members = [s for s in subs if dom[s] == d and s not in FIG3_EXCLUDE]
        for key, color, name, src in (("rå", RAW, "Rå ordtelling", raw_tok), ("levd", LIVED, "Bekreftet levd", lived)):
            ys = []
            for p in PERIODS:
                bk = {u for s in members for u in src[s] if p[0] <= year.get(u, 0) <= p[1]}
                ys.append(100 * len(bk) / n_period[p])
                trows.append({"domene": d, "periode": f"{p[0]}–{p[1]}", "mål": key, "bøker": len(bk),
                              "titler": n_period[p], "per100": 100 * len(bk) / n_period[p]})
            ax.plot(range(5), ys, color=color, lw=2, marker="o", ms=4, label=name)
        ax.set_title(DOMAIN_NO[d], loc="left", fontsize=9, color=INK)
        ax.set_xticks(range(5), labels, fontsize=7.5)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
    axes[0].set_ylabel("Bøker per 100 titler")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper left", bbox_to_anchor=(0.01, 0.99), ncol=2, frameon=False, fontsize=8)
    fig.suptitle("Spredning over tid: andel bøker med minoritetsmarkører, før og etter tolkning",
                 x=0.01, ha="left", fontsize=11, color=INK, y=1.08)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(args.out / "fig3_over_tid.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # ---------- Fig 5: intensity over time by domain ----------
    # Domain-level b_w = hits in the domain's books / books with a hit, per period.
    fig, axes = plt.subplots(1, 5, figsize=(12, 3.3), sharey=True)
    for ax, d in zip(axes, DOMAIN_NO):
        members = [s for s in subs if dom[s] == d and s not in FIG3_EXCLUDE]
        for key, color, name, src in (("rå", RAW, "Rå ordtelling", raw_tok), ("levd", LIVED, "Bekreftet levd", lived)):
            ys, ns = [], []
            for p in PERIODS:
                per_book = Counter()
                for s in members:
                    for u, c in src[s].items():
                        if p[0] <= year.get(u, 0) <= p[1]:
                            per_book[u] += c
                df_, tf_ = len(per_book), sum(per_book.values())
                ys.append(tf_ / df_ if df_ else float("nan"))
                ns.append(df_)
                trows.append({"domene": d, "periode": f"{p[0]}–{p[1]}", "mål": f"bw_{key}", "bøker": df_,
                              "titler": n_period[p], "per100": tf_ / df_ if df_ else ""})
            ax.plot(range(5), ys, color=color, lw=2, marker="o", ms=4, label=name)
            if key == "levd":
                for x_, y_, n_ in zip(range(5), ys, ns):
                    ax.annotate(f"n={n_}", (x_, y_), xytext=(0, -11), textcoords="offset points",
                                ha="center", fontsize=6.5, color=INK2)
        ax.set_title(DOMAIN_NO[d], loc="left", fontsize=9, color=INK)
        ax.set_xticks(range(5), labels, fontsize=7.5)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
    axes[0].set_ylabel("Treff per bok med treff (b_w)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper left", bbox_to_anchor=(0.01, 0.99), ncol=2, frameon=False, fontsize=8)
    fig.suptitle("Intensitet over tid: hvor ofte minoritetsmarkørene nevnes i bøkene der de forekommer",
                 x=0.01, ha="left", fontsize=11, color=INK, y=1.08)
    fig.text(0.01, -0.04, "n = antall bøker med bekreftet levd treff i perioden. Felles y-akse for alle domener.",
             fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(args.out / "fig5_intensitet_over_tid.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # ---------- Fig 4: co-occurrence of lived identities ----------
    keep = [s for s in subs if len(lived[s]) >= 15 and s not in {"jodedom_tora_test"}]
    sets = {s: set(lived[s]) for s in keep}
    M = [[(len(sets[a] & sets[b]) / len(sets[a] | sets[b])) if a != b else float("nan") for b in keep] for a in keep]
    fig, ax = plt.subplots(figsize=(8.2, 7.4))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    cmap.set_bad(GRID)
    vmax = max(v for row in M for v in row if v == v)
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=vmax)
    ax.set_xticks(range(len(keep)), [LABEL[s] for s in keep], rotation=60, ha="right", fontsize=7)
    ax.set_yticks(range(len(keep)), [LABEL[s] for s in keep], fontsize=7)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    # domain separators
    pos = 0
    for d in DOMAIN_NO:
        n = sum(1 for s in keep if dom[s] == d)
        pos += n
        if pos < len(keep):
            ax.axhline(pos - 0.5, color=SURF, lw=2); ax.axvline(pos - 0.5, color=SURF, lw=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Overlapp i bøker (Jaccard)", color=INK2); cb.outline.set_visible(False)
    ax.set_title("Hvilke levde identiteter opptrer i de samme bøkene", loc="left", fontsize=11, color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(args.out / "fig4_samforekomst.png", dpi=200)
    plt.close(fig)
    pairs = sorted(((M[i][j], keep[i], keep[j]) for i in range(len(keep)) for j in range(i + 1, len(keep))
                    if dom[keep[i]] != dom[keep[j]]), reverse=True)[:8]

    with (args.out / "tall_figurer.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    with (args.out / "tall_over_tid.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(trows[0]))
        w.writeheader(); w.writerows(trows)
    print(f"Figurer skrevet til {args.out} ({N} bøker, {n_dropped} senere utgaver utelatt)")
    print("Sterkeste samforekomst på tvers av domener (Jaccard):")
    for v, a, b in pairs:
        print(f"  {v:.3f}  {a} – {b}")


if __name__ == "__main__":
    main()
