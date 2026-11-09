import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SYSTEM_PROMPT = """Du annoterer hvert tekstfragment uavhengig etter Luminon-rammeverket.

Fragmentene har formen A<b>X</b>B der X (mellom markørene) er målordet du skal beskrive.
Bruk konteksten før/etter som støtte, men alle felt skal gjelde selve X.

TOPP-NED – kategorier:
1. "kategori" (hvordan X brukes semantisk/kontekstuelt):
   Hvis X er et religiøst ord/markør ([religion]):
   - "levd_praksis": Faktisk religiøs praksis, tro, bønn, rituale eller aktiv deltakelse (f.eks. "går i moskeen hver uke", "ba til Gud", "feiret sabbat").
   - "identitetsmarkør": Beskriver en karakters eller gruppes sosiale, etniske eller kulturelle tilhørighet/identitet uten fokus på selve trosutøvelsen (f.eks. "en muslimsk jente", "han er jøde").
   - "romlig_kulisse": Bygning eller markør brukt som fysisk/geografisk kulisse, veimarkør eller stedsangivelse (f.eks. "kinoen ligger bak moskeen", "gikk forbi kirken").
   - "historisk_tematisk": Historisk ramme (f.eks. 2. verdenskrig/Holocaust, vikingtid) eller overordnet faglig/tematisk omtale.
   - "sekulær_høytid_utrop": Sekulær høytidsmarkering eller fast uttrykk/utrop ("Herregud").
   - "uten-relevans": Homonym (f.eks. jentenavnet "Tora", etternavn, OCR-støy) som ikke har med religion å gjøre.

   Hvis X er et ord knyttet til funksjonsnedsettelse/hjelpemiddel ([funksjon]):
   - "faktisk_funksjonsnedsettelse": Faktisk varig fysisk eller sensorisk funksjonsnedsettelse/tilstand eller bruk av hjelpemiddel hos en person/karakter (f.eks. "hun er blind og bruker stokk", "sitter i rullestol", "snakker tegnspråk").
   - "forbigående_skade": Midlertidig skade eller fysisk situasjon (f.eks. krykker etter beinbrudd, blendet av lys, lukkede øyne).
   - "metaforisk": Metaforisk, billedlig eller idiomatisk bruk (f.eks. "blind av raseri", "døv for argumenter", "lammet av skrekk", "blindvei").
   - "objekt_miljø": Omtale av hjelpemiddel/gjenstand som løsrevet objekt eller kulisse uten tilknytning til en person med funksjonsnedsettelse.
   - "uten-relevans": Homonym (f.eks. dyret "et lam", lammekjøtt, annet ord) eller støy.

2. "litterær_funksjon" (i tråd med DHNB 2027-spørsmålene):
   Velg KUN én av:
   - "anerkjennelse_agens": Karakter med agens, subjektivitet eller gjenkjennelig hverdagsliv.
   - "markert_annerledeshet": Eksplisitt markert som fremmed, problematisk, eksotisk eller stereotypisk.
   - "bakgrunnsnorm": Umarkert bakgrunnsnorm eller hverdagsdetalj.
   - "historisk_opplysende": Historisk, konfliktorientert eller forklarende omtale.
   - "ikke_bokstavelig": Ikke-bokstavelig (metafor, homonym, rent stedsnavn/veimarkør).

BUNN-OPP – karakteristikker (alltid knyttet til X, ikke til fragmentet som helhet):
- "karakteristikker_generert": inntil 3 korte norske stikkord formulert med dine egne ord, som karakteriserer X i denne konteksten (f.eks. ["veimarkør", "byrom"], ["metafor", "sinne"], ["familie", "hverdagsliv"], ["2_verdenskrig", "forfølgelse"], ["fornavn", "jente"]).
- "karakteristikker_fragment": inntil 3 ord eller korte uttrykk hentet ORDRETT fra fragmentet (ikke X selv), som er relevante for X.

Formatkrav (viktig):
- Du får linjer på formen "<id> | [<domain>] <fragment>".
- Du skal alltid svare med KUN ÉN gyldig JSON-struktur med nøkkelen "items":
{
  "items": [
    {
      "id": "<samme id som i input>",
      "kategori": "<verdi>",
      "litterær_funksjon": "<verdi>",
      "karakteristikker_generert": ["...", "..."],
      "karakteristikker_fragment": ["...", "..."],
      "begrunnelse": "<maks 15 ord>"
    }
  ]
}
"""

def get_gemini_key() -> str:
    raw = os.environ.get("GEMINI_API_KEY", "").strip()
    m = re.search(r"(AIza[0-9A-Za-z\-_]{35})", raw)
    if m:
        return m.group(1)
    return raw.strip("'").strip('"').strip().split()[0] if raw else ""

def annotate_batch(batch: list[dict], api_key: str, model: str = "gemini-2.5-flash") -> list[dict]:
    user_msg = "\n".join(f'{item["id"]} | [{item["domain"]}] {item["concordance"]}' for item in batch)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            content = res["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)
            anns = parsed.get("items", []) if isinstance(parsed, dict) else parsed
            ann_by_id = {str(a["id"]): a for a in anns if isinstance(a, dict) and "id" in a}
            merged = []
            for item in batch:
                a = ann_by_id.get(str(item["id"]), {})
                merged.append({
                    **item,
                    "model": f"gemini/{model}",
                    "kategori": a.get("kategori", "ukjent"),
                    "litterær_funksjon": a.get("litterær_funksjon", "ukjent"),
                    "karakteristikker_generert": a.get("karakteristikker_generert", []),
                    "karakteristikker_fragment": a.get("karakteristikker_fragment", []),
                    "begrunnelse": a.get("begrunnelse", ""),
                })
            return merged
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise RuntimeError(f"HTTP {e.code}: {e.reason}") from e
            if attempt == 3:
                print(f"Batch failed after retries: HTTP {e.code}: {e}")
                return []
            time.sleep(2.0 * (attempt + 1))
        except Exception as e:
            if attempt == 3:
                print(f"Batch failed after retries: {type(e).__name__}: {e}")
                return []
            time.sleep(2.0 * (attempt + 1))
    return []

def build_summary(records: list[dict]) -> dict:
    summary = {}
    by_sub = defaultdict(list)
    for r in records:
        by_sub[r["subgroup"]].append(r)

    for sub, items in sorted(by_sub.items()):
        cat_counts = Counter(x["kategori"] for x in items)
        stance_counts = Counter(x["litterær_funksjon"] for x in items)
        char_gen_counts = Counter(
            str(c).lower() for x in items for c in (x.get("karakteristikker_generert") or [])
        )
        char_frag_counts = Counter(
            str(c).lower() for x in items for c in (x.get("karakteristikker_fragment") or [])
        )
        pre_2010 = Counter(x["kategori"] for x in items if x["year"] < 2010)
        post_2010 = Counter(x["kategori"] for x in items if x["year"] >= 2010)
        summary[sub] = {
            "total": len(items),
            "kategori": dict(cat_counts.most_common()),
            "litterær_funksjon": dict(stance_counts.most_common()),
            "top_karakteristikker_generert": dict(char_gen_counts.most_common(12)),
            "top_karakteristikker_fragment": dict(char_frag_counts.most_common(12)),
            "kategori_2000_2009": dict(pre_2010.most_common()),
            "kategori_2010_2024": dict(post_2010.most_common()),
        }
    return summary

def main():
    api_key = get_gemini_key()
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment")

    in_path = Path("outputs/concordances_for_luminon.jsonl")
    out_path = Path("outputs/luminon_annotations.jsonl")
    sum_path = Path("outputs/luminon_summary.json")

    all_items = [json.loads(line) for line in in_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    done_ids = set()
    existing_records = []
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                if rec.get("kategori") not in (None, "ukjent", "unknown"):
                    done_ids.add(rec["id"])
                    existing_records.append(rec)

    todo = [item for item in all_items if item["id"] not in done_ids]
    print(f"Total fragments: {len(all_items)} | Already annotated: {len(done_ids)} | Remaining: {len(todo)}")

    batch_size = 25
    batches = [todo[i : i + batch_size] for i in range(0, len(todo), batch_size)]

    lock = threading.Lock()
    completed = 0

    with out_path.open("a", encoding="utf-8") as out_f:
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(annotate_batch, b, api_key) for b in batches]
            for fut in as_completed(futures):
                res = fut.result()
                with lock:
                    for r in res:
                        out_f.write(json.dumps(r, ensure_ascii=False) + "\n")
                        existing_records.append(r)
                    out_f.flush()
                    completed += 1
                    if completed % 10 == 0 or completed == len(batches):
                        print(f"Completed {completed}/{len(batches)} batches ({len(existing_records)}/{len(all_items)} items)", flush=True)

    summary = build_summary(existing_records)
    sum_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved summary to {sum_path}", flush=True)

if __name__ == "__main__":
    main()
