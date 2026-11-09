#!/usr/bin/env python3
"""Review sheet for candidate markers: precision per candidate plus example windows.

  python scripts/make_marker_sheet.py --dir outputs/markers --out outputs/markers/kandidatmarkorer_pilot.xlsx
"""

import argparse
import collections
import json
import math
import random
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

F = Font(name="Arial", size=10)
FB = Font(name="Arial", size=10, bold=True)
FH = Font(name="Arial", size=10, bold=True, color="FFFFFF")
FEX = Font(name="Arial", size=10, italic=True, color="808080")
HEAD = PatternFill("solid", fgColor="1F3864")
INPUT = PatternFill("solid", fgColor="FFF2CC")
WRAP = Alignment(wrap_text=True, vertical="top")
PCT = "0%"


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - h) / d), min(1.0, (c + h) / d)


def show(c):
    return re.sub(r"<b>(.*?)</b>", r"[\1]", c, flags=re.I)


def header(ws, names, widths):
    for j, (n, w) in enumerate(zip(names, widths), 1):
        c = ws.cell(row=1, column=j, value=n)
        c.font, c.fill, c.alignment = FH, HEAD, Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "A2"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=Path("outputs/markers"))
    ap.add_argument("--candidates", type=Path, default=Path("data/kandidatmarkorer_pilot.json"))
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--examples", type=int, default=6)
    args = ap.parse_args()

    spec = {"kand_" + c["ord"][0]: c for c in json.loads(args.candidates.read_text(encoding="utf-8"))["kandidater"]}
    total, books, meta = collections.Counter(), collections.defaultdict(set), {}
    for line in (args.dir / "conc" / "concordances_full.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        total[r["subgroup"]] += 1
        books[r["subgroup"]].add(r["urn"])
        meta[r["id"]] = (r.get("title", ""), r.get("year"))
    ann = collections.defaultdict(list)
    for line in (args.dir / f"annotert_{args.model}.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("makro"):
            ann[r["subgroup"]].append(r)

    wb = Workbook()
    ws = wb.active
    ws.title = "Les meg"
    ws.column_dimensions["A"].width = 110
    text = [
        ("Kandidatmarkører – pilot (funksjonsnedsettelse og flerkulturelt)", Font(name="Arial", size=14, bold=True)),
        ("", F),
        ("Kandidatene er funnet på fem måter: ord som er overrepresentert i tekstblokker med eksisterende markører (blokk), ord som skiller "
         "bøker med levd treff fra referansebøker (ramme), samforekomstklynger (galakse), modellens kontekstord (kontekst), "
         "jokertegnsøk etter sammensetninger i DHLAB (sammensetning) og forslag fra fagkunnskap (domene). To kontrollord forventes å ha lav presisjon.", F),
        ("", F),
        (f"For hver kandidat er alle treff i korpuset hentet, og inntil 60 vinduer er annotert med {args.model} (skjema v2.2). "
         "Levd-andel er andelen av de annoterte vinduene med makroklasse levd, med 95 % konfidensintervall (Wilson). "
         "Bøker er antall bøker i korpuset med minst ett treff.", F),
        ("", F),
        ("Gule celler er til deg: velg behold / forkast / usikker i fanen Kandidater, og kommenter gjerne eksemplene.", F),
        ("Vinduene er korte utdrag fra opphavsrettslig beskyttede bøker og er bare for internt forskningsarbeid.", F),
    ]
    for i, (t, f) in enumerate(text, 1):
        c = ws.cell(row=i, column=1, value=t)
        c.font, c.alignment = f, WRAP

    ws = wb.create_sheet("Kandidater")
    cols = ["Domene", "Kandidat", "Ordformer", "Kilde", "Vinduer i korpuset", "Bøker", "Annotert", "Levd (n)", "Levd-andel",
            "KI nedre", "KI øvre", "Vanligste kategori", "Vanligste underkategori", "Din vurdering", "Kommentar"]
    header(ws, cols, [14, 20, 36, 26, 11, 8, 9, 8, 10, 9, 9, 28, 26, 14, 40])
    dv = DataValidation(type="list", formula1='"behold,forkast,usikker"', allow_blank=True)
    ws.add_data_validation(dv)
    order = sorted(ann, key=lambda s: (spec[s]["domene"], -sum(r["makro"] == "lived" for r in ann[s]) / len(ann[s])))
    for i, s in enumerate(order, 2):
        rr = ann[s]
        k = sum(r["makro"] == "lived" for r in rr)
        lo, hi = wilson(k, len(rr))
        kat = collections.Counter(r["kategori"] for r in rr).most_common(1)[0][0]
        sub = collections.Counter(r.get("underkategori") for r in rr if r.get("underkategori")).most_common(1)
        vals = [spec[s]["domene"], s[5:], ", ".join(spec[s]["ord"]), ", ".join(spec[s]["kilde"]), total[s], len(books[s]),
                len(rr), k, f"=H{i}/G{i}", lo, hi, kat, sub[0][0] if sub else "–"]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=i, column=j, value=v)
            c.font, c.alignment = F, WRAP
        for j in (9, 10, 11):
            ws.cell(row=i, column=j).number_format = PCT
        for j in (14, 15):
            ws.cell(row=i, column=j).fill = INPUT
        dv.add(ws.cell(row=i, column=14))
    ws.auto_filter.ref = f"A1:O{len(order) + 1}"

    ws = wb.create_sheet("Eksempler")
    cols = ["Kandidat", "År", "Tittel", "Vindu", "Kategori", "Underkategori", "Makro", "Begrunnelse (modell)", "Stemmer? (ja/nei)", "Kommentar"]
    header(ws, cols, [18, 6, 26, 64, 26, 22, 9, 40, 12, 36])
    dv2 = DataValidation(type="list", formula1='"ja,nei,delvis"', allow_blank=True)
    ws.add_data_validation(dv2)
    rng = random.Random(2027)
    row = 2
    for s in order:
        rr = sorted(ann[s], key=lambda r: r["id"])
        lived = [r for r in rr if r["makro"] == "lived"]
        other = [r for r in rr if r["makro"] != "lived"]
        rng.shuffle(lived)
        rng.shuffle(other)
        half = args.examples // 2
        pick = lived[:half] + other[: args.examples - min(half, len(lived))]
        for r in sorted(pick[: args.examples], key=lambda r: r["year"]):
            t, y = meta.get(r["id"], ("", r["year"]))
            vals = [s[5:], y, t, show(r["concordance"]), r["kategori"], r.get("underkategori") or "–",
                    r["makro"], r.get("begrunnelse", "")]
            for j, v in enumerate(vals, 1):
                c = ws.cell(row=row, column=j, value=v)
                c.font, c.alignment = F, WRAP
            for j in (9, 10):
                ws.cell(row=row, column=j).fill = INPUT
            dv2.add(ws.cell(row=row, column=9))
            row += 1
    ws.auto_filter.ref = f"A1:J{row - 1}"

    from openpyxl.workbook.properties import CalcProperties
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.save(args.out)
    print(f"Skrev {args.out}: {len(order)} kandidater, {row - 2} eksempler")


if __name__ == "__main__":
    main()
