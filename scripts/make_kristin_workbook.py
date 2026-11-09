#!/usr/bin/env python3
"""Build a review workbook (top-down only) from the full v2.2 Luminon run.

  python scripts/make_kristin_workbook.py \
      --main outputs/full_v22/haikumed.jsonl \
      --refs pro=outputs/full_v22/pro_ref.jsonl opus=outputs/full_v22/opus_ref.jsonl \
      --out outputs/full_v22/luminon_v22_gjennomgang.xlsx

Sheets: Les meg, Oversikt, Over tid, Kategorier, Enighet, Revisjon, Lesestikk.
Counts are computed here from the annotation files; percentages and rates are
Excel formulas over those counts. Only short concordance windows (<= 25 words)
are included, and only in Revisjon and Lesestikk (a few hundred), not the full set.
"""

import argparse
import itertools
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
import luminon_schema_v2 as S  # noqa: E402
from harvest_full_concordances import load_corpus  # noqa: E402
from lexicon_dhnb2027 import LEXICON  # noqa: E402

MACROS = ["lived", "thematic", "backdrop", "other"]
MACRO_NO = {"lived": "levd", "thematic": "tematisk", "backdrop": "kulisse", "other": "annet"}
PERIODS = [(2000, 2004), (2005, 2009), (2010, 2014), (2015, 2019), (2020, 2024)]
V1_FILES = [Path("outputs/luminon_annotations.jsonl"), Path("outputs/luminon_round2_annotations.jsonl")]

FONT = "Arial"
F_BASE = Font(name=FONT, size=10)
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_TITLE = Font(name=FONT, size=14, bold=True)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_EX = Font(name=FONT, size=10, italic=True, color="808080")
FILL_HEAD = PatternFill("solid", fgColor="1F3864")
FILL_INPUT = PatternFill("solid", fgColor="FFF2CC")
WRAP = Alignment(wrap_text=True, vertical="top")
PCT = "0.0%"


def show(conc: str) -> str:
    """Readable window: target word in [brackets] instead of <b>…</b>."""
    return re.sub(r"<b>(.*?)</b>", r"[\1]", conc, flags=re.IGNORECASE)


def load(path):
    rows = [json.loads(line) for line in Path(path).open(encoding="utf-8")]
    return {r["id"]: r for r in rows if r.get("kategori") in S.CATEGORIES.get(r["domain"], {})}


def kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] / n * cb[k] / n for k in set(a) | set(b))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def header(ws, row, names, widths=None):
    for j, name in enumerate(names, 1):
        c = ws.cell(row=row, column=j, value=name)
        c.font, c.fill, c.alignment = F_HEAD, FILL_HEAD, Alignment(wrap_text=True, vertical="center")
        if widths:
            ws.column_dimensions[get_column_letter(j)].width = widths[j - 1]
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def style_body(ws, first_row):
    for row in ws.iter_rows(min_row=first_row):
        for c in row:
            if c.font is None or not c.font.bold:
                c.font = F_BASE if c.font.color is None or c.font.color.rgb in (None, "FF000000") else c.font


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main", type=Path, required=True)
    ap.add_argument("--refs", nargs="*", default=[], metavar="NAME=PATH")
    ap.add_argument("--corpus", type=Path, default=Path("data/barn.csv"))
    ap.add_argument("--concordances", type=Path, default=Path("outputs/full_fiction/concordances_full.jsonl"),
                    help="source of title/authors (kept out of the annotation files)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--per-cell", type=int, default=3, help="windows per subgroup x kategori in Lesestikk")
    args = ap.parse_args()

    meta = {}
    for line in args.concordances.open(encoding="utf-8"):
        r = json.loads(line)
        meta[r["id"]] = (r.get("title", ""), r.get("authors", ""))
    main_rows = load(args.main)
    main_name = json.loads(args.main.open().readline())["model"]
    refs = {}
    for spec in args.refs:
        n, p = spec.split("=", 1)
        refs[n] = load(p)
    books = load_corpus(args.corpus, 2000, 2024)
    titles_per_period = Counter()
    for b in books.values():
        for p0, p1 in PERIODS:
            if p0 <= b["year"] <= p1:
                titles_per_period[(p0, p1)] += 1

    v1 = {}
    for p in V1_FILES:
        if p.exists():
            for line in p.open(encoding="utf-8"):
                r = json.loads(line)
                v1[r["id"]] = S.macro_of(r["domain"], r["kategori"])

    words_of = {s: ws for _, s, ws in LEXICON}
    dom_of = {s: d for d, s, _ in LEXICON}
    by_sub = defaultdict(list)
    for r in main_rows.values():
        by_sub[r["subgroup"]].append(r)
    subs = [s for _, s, _ in LEXICON if s in by_sub]

    wb = Workbook()

    # ---------------- Les meg ----------------
    ws = wb.active
    ws.title = "Les meg"
    ws.column_dimensions["A"].width = 110
    n_ref = len(set.intersection(*(set(v) for v in refs.values()))) if refs else 0
    lines = [
        ("Luminon v2.2 – gjennomgang av fullt uttrekk (topp-ned)", F_TITLE),
        ("", F_BASE),
        (f"Korpus: {len(books)} ikke-oversatte skjønnlitterære barne- og ungdomsbøker på bokmål, 2000–2024 (data/barn.csv etter Kristins redigeringer).", F_BASE),
        (f"Konkordanser: {len(main_rows)} vinduer (≤ 25 ord) for 34 undergrupper i fem domener – alle treff, ikke utvalg.", F_BASE),
        (f"Annotering: {main_name} (Anthropic, effort medium) på alle vinduer, skjema {S.SCHEMA_VERSION}. "
         f"Referansemodeller ({', '.join(refs)}) på et stratifisert utvalg på {n_ref} vinduer (30 per undergruppe, fordelt på femårsperioder).", F_BASE),
        ("Bare topp-ned-feltene (kategori, underkategori, makroklasse, referent, litterær funksjon) er brukt her. Bunn-opp-ordene venter.", F_BASE),
        ("", F_BASE),
        ("Faner", F_BOLD),
        ("Oversikt – makroklasser per undergruppe, med abstraktets andel levd og referansemodellenes andel til sammenligning.", F_BASE),
        ("Over tid – spredning (bøker med levd-treff per 100 titler) og intensitet (b_w = levd-treff per bok med levd-treff) per femårsperiode.", F_BASE),
        ("Kategorier – fordeling på kategori og underkategori per undergruppe.", F_BASE),
        ("Enighet – kappa mellom modellene på referanseutvalget, og mot abstraktets etiketter.", F_BASE),
        ("Revisjon – vinduer der modellene er uenige om makroklasse. Her trengs din vurdering.", F_BASE),
        ("Lesestikk – inntil tre vinduer per undergruppe og kategori, for å lese om etikettene gir mening.", F_BASE),
        ("", F_BASE),
        ("Slik fyller du inn", F_BOLD),
        ("Gule celler er til deg. I Revisjon velger du riktig makroklasse fra nedtrekkslisten og skriver gjerne kategori og kommentar. "
         "I Lesestikk svarer du ja/nei på om etiketten stemmer. Øverste rad i Revisjon er et eksempel (grå kursiv).", F_BASE),
        ("", F_BASE),
        ("Makroklasser", F_BOLD),
    ] + [(f"{MACRO_NO[m]} ({m}): {S.MACRO[m]}", F_BASE) for m in MACROS] + [
        ("", F_BASE),
        ("Merk", F_BOLD),
        ("Tellingene er beregnet fra annoteringsfilene; prosenter og rater er formler over tellingene. "
         "45 titler finnes i to utgaver og telles begge – de er ikke fjernet ennå.", F_BASE),
        ("Vinduene er korte utdrag fra opphavsrettslig beskyttede bøker. Arbeidsboka er for internt forskningsarbeid og skal ikke publiseres.", F_BASE),
    ]
    for i, (text, font) in enumerate(lines, 1):
        c = ws.cell(row=i, column=1, value=text)
        c.font, c.alignment = font, Alignment(wrap_text=True, vertical="top")

    # ---------------- Oversikt ----------------
    ws = wb.create_sheet("Oversikt")
    cols = ["Domene", "Undergruppe", "Ord i søket", "Vinduer", "Bøker"] + \
           [f"{MACRO_NO[m]} (n)" for m in MACROS] + [f"{MACRO_NO[m]} %" for m in MACROS] + \
           ["Abstrakt: levd % (utvalg)", "Abstrakt n", "Referanser: levd % (utvalg)", "Referanser n", "Kommentar"]
    header(ws, 1, cols, [18, 24, 40, 9, 8, 9, 10, 9, 9, 9, 10, 9, 9, 13, 10, 14, 11, 40])
    for i, s in enumerate(subs, 2):
        rr = by_sub[s]
        c = Counter(r["makro"] for r in rr)
        old = [v1[r["abstract_sample_id"]] for r in rr if r.get("abstract_sample_id") in v1]
        ref_m = [refs[n][r["id"]]["makro"] for n in refs for r in rr if r["id"] in refs[n]]
        vals = [dom_of[s], s, ", ".join(words_of[s]), len(rr), len({r["urn"] for r in rr})] + [c[m] for m in MACROS]
        for j, v in enumerate(vals, 1):
            ws.cell(row=i, column=j, value=v)
        for k in range(4):
            col = get_column_letter(6 + k)
            cell = ws.cell(row=i, column=10 + k, value=f"=IFERROR({col}{i}/$D{i},0)")
            cell.number_format = PCT
        ws.cell(row=i, column=14, value=(old.count("lived") / len(old)) if old else None).number_format = PCT
        ws.cell(row=i, column=15, value=len(old))
        ws.cell(row=i, column=16, value=(ref_m.count("lived") / len(ref_m)) if ref_m else None).number_format = PCT
        ws.cell(row=i, column=17, value=len(ref_m))
        ws.cell(row=i, column=18).fill = FILL_INPUT
    last = len(subs) + 1
    tr = last + 1
    ws.cell(row=tr, column=2, value="Totalt").font = F_BOLD
    for col in range(4, 10):
        L = get_column_letter(col)
        ws.cell(row=tr, column=col, value=f"=SUM({L}2:{L}{last})").font = F_BOLD
    for k in range(4):
        col = get_column_letter(6 + k)
        ws.cell(row=tr, column=10 + k, value=f"=IFERROR({col}{tr}/$D{tr},0)").number_format = PCT
    ws.cell(row=1, column=14).comment = Comment("Andel levd blant abstraktets annoteringer (v1, gemini-2.5-flash) for de samme vinduene. "
                                                "v1-kategoriene er oversatt til makroklasse med samme tabell som figurene i abstraktet.", "Claude")
    ws.cell(row=1, column=16).comment = Comment("Andel levd hos referansemodellene på referanseutvalget (begge modeller samlet).", "Claude")
    ws.auto_filter.ref = f"A1:R{last}"

    # ---------------- Over tid ----------------
    ws = wb.create_sheet("Over tid")
    cols = ["Domene", "Undergruppe", "Periode", "Titler i perioden (N)", "Vinduer", "Bøker med treff",
            "Levd-vinduer (TF)", "Bøker med levd-treff (DF)", "Andel levd", "DF per 100 titler", "b_w = TF/DF"]
    header(ws, 1, cols, [18, 24, 11, 12, 9, 10, 11, 12, 10, 11, 11])
    row = 2
    for s in subs:
        for p0, p1 in PERIODS:
            rr = [r for r in by_sub[s] if p0 <= r["year"] <= p1]
            lived = [r for r in rr if r["makro"] == "lived"]
            vals = [dom_of[s], s, f"{p0}–{p1}", titles_per_period[(p0, p1)], len(rr), len({r["urn"] for r in rr}),
                    len(lived), len({r["urn"] for r in lived})]
            for j, v in enumerate(vals, 1):
                ws.cell(row=row, column=j, value=v)
            ws.cell(row=row, column=9, value=f"=IFERROR(G{row}/E{row},0)").number_format = PCT
            ws.cell(row=row, column=10, value=f"=IFERROR(H{row}/D{row}*100,0)").number_format = "0.00"
            ws.cell(row=row, column=11, value=f'=IFERROR(G{row}/H{row},"")').number_format = "0.00"
            row += 1
    ws.auto_filter.ref = f"A1:K{row - 1}"
    ws.cell(row=row + 1, column=1, value="N = antall titler i korpuset per periode (data/barn.csv, skjønn, nob). "
                                         "TF/DF teller bekreftede levd-vinduer og unike bøker; b_w som i abstraktet (Katz 1996).").font = F_EX

    # ---------------- Kategorier ----------------
    ws = wb.create_sheet("Kategorier")
    cols = ["Domene", "Undergruppe", "Kategori", "Underkategori", "Makroklasse", "Vinduer", "Andel av undergruppen"]
    header(ws, 1, cols, [18, 24, 30, 28, 12, 9, 12])
    row = 2
    for s in subs:
        c = Counter((r["kategori"], r.get("underkategori") or "–") for r in by_sub[s])
        for (k, u), n in sorted(c.items(), key=lambda x: (-x[1])):
            for j, v in enumerate([dom_of[s], s, k, u, MACRO_NO[S.macro_of(dom_of[s], k)], n], 1):
                ws.cell(row=row, column=j, value=v)
            ws.cell(row=row, column=7, value=f"=F{row}/SUMIFS($F:$F,$B:$B,B{row})").number_format = PCT
            row += 1
    ws.auto_filter.ref = f"A1:G{row - 1}"

    # ---------------- Enighet ----------------
    ws = wb.create_sheet("Enighet")
    header(ws, 1, ["Par", "Felt", "n", "Andel enig", "Kappa"], [34, 20, 8, 12, 10])
    runs = {main_name: main_rows, **refs}
    row = 2
    for a, b in itertools.combinations(runs, 2):
        ids = sorted(set(runs[a]) & set(runs[b]))
        for f in ["kategori", "makro", "underkategori", "referent", "litterær_funksjon"]:
            use = ids
            if f == "underkategori":
                use = [i for i in ids if runs[a][i]["kategori"] == runs[b][i]["kategori"]
                       and S.subcategories(runs[a][i]["domain"], runs[a][i]["kategori"])]
            x = [runs[a][i].get(f) for i in use]
            y = [runs[b][i].get(f) for i in use]
            if not use:
                continue
            for j, v in enumerate([f"{a} – {b}", f, len(use), sum(p == q for p, q in zip(x, y)) / len(use), kappa(x, y)], 1):
                ws.cell(row=row, column=j, value=v)
            ws.cell(row=row, column=4).number_format = PCT
            ws.cell(row=row, column=5).number_format = "0.000"
            row += 1
    for name, rows_ in runs.items():
        ids = [i for i, r in rows_.items() if r.get("abstract_sample_id") in v1]
        if ids:
            x = [v1[rows_[i]["abstract_sample_id"]] for i in ids]
            y = [rows_[i]["makro"] for i in ids]
            for j, v in enumerate([f"{name} – abstrakt (v1)", "makro", len(ids), sum(p == q for p, q in zip(x, y)) / len(ids), kappa(x, y)], 1):
                ws.cell(row=row, column=j, value=v)
            ws.cell(row=row, column=4).number_format = PCT
            ws.cell(row=row, column=5).number_format = "0.000"
            row += 1
    ws.cell(row=row + 1, column=1, value="Kappa er beregnet i Python (Cohens kappa) fra annoteringsfilene. "
                                         "Underkategori telles bare der begge modellene valgte samme kategori.").font = F_EX

    # ---------------- Revisjon ----------------
    ws = wb.create_sheet("Revisjon")
    names = list(runs)
    cols = ["id", "Domene", "Undergruppe", "År", "Tittel", "Forfatter", "Vindu"] + \
           [f"{n}: {x}" for n in names for x in ("kategori", "underkategori", "makro")] + \
           ["Din makroklasse", "Din kategori", "Kommentar"]
    widths = [24, 16, 20, 6, 26, 22, 60] + [20, 18, 10] * len(names) + [14, 22, 40]
    header(ws, 1, cols, widths)
    ex = ["EKSEMPEL", "religion", "moske_bygg", 2016, "(eksempeltittel)", "(eksempelforfatter)",
          "Etter bønnen serverer [moskeen] ris og kylling …"] + \
         ["levd_praksis", "–", "levd", "romlig_kulisse", "sosialt_hverdagsrom", "kulisse", "levd_praksis", "–", "levd"][:3 * len(names)] + \
         ["levd", "levd_praksis", "Fellesmåltid etter bønn er religiøs praksis, ikke kulisse."]
    for j, v in enumerate(ex, 1):
        c = ws.cell(row=2, column=j, value=v)
        c.font, c.alignment = F_EX, WRAP
    shared = sorted(set.intersection(*(set(runs[n]) for n in names)),
                    key=lambda i: (runs[names[0]][i]["subgroup"], runs[names[0]][i]["year"]))
    dv = DataValidation(type="list", formula1='"levd,tematisk,kulisse,annet,usikker"', allow_blank=True)
    ws.add_data_validation(dv)
    row = 3
    for i in shared:
        if len({runs[n][i]["makro"] for n in names}) < 2:
            continue
        r0 = runs[names[0]][i]
        vals = [i, r0["domain"], r0["subgroup"], r0["year"], *meta.get(i, ("", "")), show(r0["concordance"])]
        for n in names:
            r = runs[n][i]
            vals += [r["kategori"], r.get("underkategori") or "–", MACRO_NO[r["makro"]]]
        for j, v in enumerate(vals, 1):
            ws.cell(row=row, column=j, value=v).alignment = WRAP
        for j in range(len(vals) + 1, len(vals) + 4):
            ws.cell(row=row, column=j).fill = FILL_INPUT
            ws.cell(row=row, column=j).alignment = WRAP
        dv.add(ws.cell(row=row, column=len(vals) + 1))
        row += 1
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{row - 1}"
    n_revisjon = row - 3

    # ---------------- Lesestikk ----------------
    ws = wb.create_sheet("Lesestikk")
    cols = ["id", "Domene", "Undergruppe", "År", "Tittel", "Vindu", "Kategori", "Underkategori", "Makroklasse",
            "Referent", "Begrunnelse (modell)", "Stemmer etiketten? (ja/nei)", "Kommentar"]
    header(ws, 1, cols, [24, 16, 20, 6, 26, 60, 24, 22, 11, 14, 40, 14, 40])
    dv2 = DataValidation(type="list", formula1='"ja,nei,delvis"', allow_blank=True)
    ws.add_data_validation(dv2)
    rng = random.Random(2027)
    row = 2
    for s in subs:
        cells = defaultdict(list)
        for r in by_sub[s]:
            cells[r["kategori"]].append(r)
        for k in S.CATEGORIES[dom_of[s]]:
            pool = sorted(cells.get(k, []), key=lambda r: r["id"])
            rng.shuffle(pool)
            for r in sorted(pool[: args.per_cell], key=lambda r: r["year"]):
                vals = [r["id"], r["domain"], s, r["year"], meta.get(r["id"], ("", ""))[0], show(r["concordance"]), r["kategori"],
                        r.get("underkategori") or "–", MACRO_NO[r["makro"]], r.get("referent"), r.get("begrunnelse", "")]
                for j, v in enumerate(vals, 1):
                    ws.cell(row=row, column=j, value=v).alignment = WRAP
                for j in (12, 13):
                    ws.cell(row=row, column=j).fill = FILL_INPUT
                dv2.add(ws.cell(row=row, column=12))
                row += 1
    ws.auto_filter.ref = f"A1:M{row - 1}"
    n_lese = row - 2

    for sheet in wb.worksheets:
        for r in sheet.iter_rows():
            for c in r:
                if c.font and (c.font.bold or c.font.italic or c.font.size != 10):
                    if c.font.name != FONT:
                        c.font = Font(name=FONT, size=c.font.size, bold=c.font.bold, italic=c.font.italic, color=c.font.color)
                    continue
                c.font = F_BASE
    # openpyxl stores no cached formula values; make Excel/Numbers compute them on open.
    from openpyxl.workbook.properties import CalcProperties
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.out)
    print(f"Skrev {args.out}: {len(subs)} undergrupper, {n_revisjon} revisjonsvinduer, {n_lese} lesestikk")


if __name__ == "__main__":
    main()
