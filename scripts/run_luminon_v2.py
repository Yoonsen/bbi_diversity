#!/usr/bin/env python3
"""Annotate concordances with Luminon schema v2 (resumable).

Input:  outputs/full_fiction/concordances_full.jsonl (from harvest_full_concordances.py)
Output: one jsonl per model; existing ids are skipped on rerun.

Only an opaque per-batch number and the <=25-word window are sent to the model
(no ids with subgroup names, no title/author/year). Invalid answers are retried
once per item in a smaller batch; remaining failures are stored with `errors`.

Examples:
  python scripts/run_luminon_v2.py --subgroups synagoge_bygg trans_kjonn --out outputs/pilot_v2/flash.jsonl
  python scripts/run_luminon_v2.py --ids-from outputs/pilot_v2/pro_sample_ids.txt \
      --model gemini-3.1-pro-preview --out outputs/pilot_v2/pro.jsonl
"""

import argparse
import json
import random
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import luminon_schema_v2 as S  # noqa: E402
from run_luminon import get_gemini_key  # noqa: E402

KEEP = ["id", "domain", "subgroup", "urn", "year", "matched_word", "concordance", "abstract_sample_id"]

# Structure only (no label enums), so both regimes are held to the same label
# validation in luminon_schema_v2.validate().
_STR_LIST = {"type": "array", "items": {"type": "string"}}
ANTHROPIC_SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "kategori": {"type": "string"},
            "litterær_funksjon": {"type": "string"},
            "underkategori": {"type": ["string", "null"]},
            "referent": {"type": "string"},
            "karakteristikker_generert": _STR_LIST,
            "kontekstord_lemma": _STR_LIST,
            "begrunnelse": {"type": "string"},
        },
        "required": ["id", "kategori", "litterær_funksjon", "underkategori", "referent",
                     "karakteristikker_generert", "kontekstord_lemma", "begrunnelse"],
        "additionalProperties": False,
    }}},
    "required": ["items"],
    "additionalProperties": False,
}
_anthropic_client = None


def anthropic_schema(bottom_up: bool) -> dict:
    schema = json.loads(json.dumps(ANTHROPIC_SCHEMA))
    item = schema["properties"]["items"]["items"]
    if not bottom_up:
        for k in S.BOTTOM_UP_FIELDS:
            item["properties"].pop(k)
            item["required"].remove(k)
    return schema


def call_model_anthropic(domain: str, batch: list[dict], model: str, effort: str, bottom_up: bool) -> dict[int, dict]:
    global _anthropic_client
    import anthropic
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(max_retries=6)
    user_msg = "\n".join(f"{i} | {item['concordance']}" for i, item in enumerate(batch))
    for attempt in range(3):
        try:
            resp = _anthropic_client.messages.create(
                model=model,
                max_tokens=16000,
                system=S.system_prompt(domain, bottom_up),
                messages=[{"role": "user", "content": user_msg}],
                output_config={"effort": effort,
                               "format": {"type": "json_schema", "schema": anthropic_schema(bottom_up)}},
            )
        except anthropic.BadRequestError as e:
            raise RuntimeError(f"HTTP 400 fra {model}: {e.message}") from e
        except (anthropic.APIStatusError, anthropic.APIConnectionError):
            time.sleep(5 * (attempt + 1))
            continue
        if resp.stop_reason == "refusal":
            print(f"  refusal fra {model} ({getattr(resp.stop_details, 'category', None)})", file=sys.stderr)
            return {}
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            items = json.loads(text).get("items", [])
        except json.JSONDecodeError:
            continue
        return {int(a["id"]): a for a in items if isinstance(a, dict) and "id" in a}
    return {}


def call_model(domain: str, batch: list[dict], api_key: str, model: str, effort: str = "low",
               bottom_up: bool = True) -> dict[int, dict]:
    if model.startswith("claude-"):
        return call_model_anthropic(domain, batch, model, effort, bottom_up)
    return call_model_gemini(domain, batch, api_key, model, bottom_up)


def call_model_gemini(domain: str, batch: list[dict], api_key: str, model: str, bottom_up: bool) -> dict[int, dict]:
    user_msg = "\n".join(f"{i} | {item['concordance']}" for i, item in enumerate(batch))
    body = {
        "systemInstruction": {"parts": [{"text": S.system_prompt(domain, bottom_up)}]},
        "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            text = res["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            items = parsed.get("items", []) if isinstance(parsed, dict) else parsed
            out = {}
            for a in items:
                try:
                    out[int(a["id"])] = a
                except (KeyError, TypeError, ValueError):
                    pass
            return out
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):
                raise RuntimeError(f"HTTP {e.code} fra {model}: {e.read()[:300]!r}") from e
            wait = 5 * (attempt + 1)
        except Exception:  # noqa: BLE001 - network/JSON hiccups: retry
            wait = 3 * (attempt + 1)
        if attempt < 4:
            time.sleep(wait)
    return {}


def annotate(domain, batch, api_key, model, run_meta):
    effort = run_meta.get("effort") or "low"
    bu = run_meta["bottom_up"]
    answers = call_model(domain, batch, api_key, model, effort, bu)
    done, retry = [], []
    for i, item in enumerate(batch):
        a = answers.get(i)
        if a and not S.validate(domain, a):
            done.append((item, a, []))
        else:
            retry.append(item)
    for item in retry:  # second chance, one at a time
        a = call_model(domain, [item], api_key, model, effort, bu).get(0) or {}
        done.append((item, a, S.validate(domain, a) if a else ["intet svar"]))
    rows = []
    for item, a, errs in done:
        k = a.get("kategori")
        rows.append({
            **{f: item.get(f) for f in KEEP},
            "kategori": k,
            "underkategori": a.get("underkategori") or None,
            "referent": a.get("referent"),
            "litterær_funksjon": a.get("litterær_funksjon"),
            "makro": S.macro_of(domain, k),
            "karakteristikker_generert": a.get("karakteristikker_generert", []),
            "kontekstord_lemma": S.clean_lemmas(a.get("kontekstord_lemma")),
            "kontekstord_raw": a.get("kontekstord_lemma", []),
            "begrunnelse": a.get("begrunnelse", ""),
            "errors": errs,
            **run_meta,
            "prompt_sha": S.prompt_sha(domain, bu),
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("outputs/full_fiction/concordances_full.jsonl"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--subgroups", nargs="*")
    ap.add_argument("--sample", nargs="*", default=[], metavar="SUBGROUP=N",
                    help="random sample of N windows from SUBGROUP (seed 42), in addition to --subgroups")
    ap.add_argument("--ids-from", type=Path, help="file with one id per line")
    ap.add_argument("--model", default="gemini-2.5-flash",
                    help="gemini-* (Google) or claude-* (Anthropic, uses ANTHROPIC_API_KEY)")
    ap.add_argument("--effort", default=None, choices=["low", "medium", "high", "xhigh", "max"],
                    help="Claude only: output_config.effort (default low)")
    ap.add_argument("--no-bottom-up", action="store_true",
                    help="top-down only: drop karakteristikker_generert and kontekstord_lemma from prompt and output")
    ap.add_argument("--batch-size", type=int, default=25)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    api_key = get_gemini_key()
    if not args.model.startswith("claude-") and not api_key:
        sys.exit("GEMINI_API_KEY mangler")

    rows = [json.loads(l) for l in args.input.open(encoding="utf-8")]
    by_sub = defaultdict(list)
    for r in rows:
        by_sub[r["subgroup"]].append(r)
    selected = []
    for s in args.subgroups or []:
        selected += by_sub[s]
    rng = random.Random(42)
    for spec in args.sample:
        s, n = spec.split("=")
        pool = list(by_sub[s])
        rng.shuffle(pool)
        selected += pool[: int(n)]
    if args.ids_from:
        want = set(args.ids_from.read_text().split())
        selected += [r for r in rows if r["id"] in want]
    selected = list({r["id"]: r for r in selected}.values())

    done_ids = set()
    if args.out.exists():
        done_ids = {json.loads(l)["id"] for l in args.out.open(encoding="utf-8")}
    todo = [r for r in selected if r["id"] not in done_ids]
    print(f"{len(selected)} valgt, {len(done_ids)} ferdig fra før, {len(todo)} å annotere med {args.model}")

    run_meta = {"model": args.model, "schema_version": S.SCHEMA_VERSION, "bottom_up": not args.no_bottom_up,
                "effort": (args.effort or "low") if args.model.startswith("claude-") else None,
                "run_id": uuid.uuid4().hex[:8], "annotated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    by_dom = defaultdict(list)
    for r in todo:
        by_dom[r["domain"]].append(r)
    batches = [(d, items[i:i + args.batch_size]) for d, items in by_dom.items()
               for i in range(0, len(items), args.batch_size)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    n_err = 0
    with args.out.open("a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(annotate, d, b, api_key, args.model, run_meta) for d, b in batches]
        for n, fut in enumerate(as_completed(futs), 1):
            res = fut.result()
            with lock:
                for r in res:
                    n_err += bool(r["errors"])
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
            if n % 5 == 0 or n == len(batches):
                print(f"  {n}/{len(batches)} batcher, {n_err} med feil", flush=True)


if __name__ == "__main__":
    main()
