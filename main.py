from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

TOKEN_RE = re.compile(r"[A-Za-zÆØÅæøå][A-Za-zÆØÅæøå\-]*")
COORD_RE = re.compile(
    r"\b([A-Za-zÆØÅæøå][A-Za-zÆØÅæøå\-]*)\s+(og|eller)\s+([A-Za-zÆØÅæøå][A-Za-zÆØÅæøå\-]*)\b",
    flags=re.IGNORECASE,
)


def normalize(word: str) -> str:
    return word.strip().lower()


def load_corpus_texts(corpus_path: Path) -> list[str]:
    if corpus_path.is_file():
        return [corpus_path.read_text(encoding="utf-8")]

    texts: list[str] = []
    for file_path in sorted(corpus_path.rglob("*.txt")):
        texts.append(file_path.read_text(encoding="utf-8"))
    return texts


def extract_vocab(texts: list[str], min_count: int) -> set[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(normalize(token) for token in TOKEN_RE.findall(text))
    return {token for token, count in counts.items() if count >= min_count}


def load_external_w2v_expansion(
    seeds: list[str],
    input_path: Path | None,
    vocab_filter: set[str] | None = None,
    min_similarity: float = 0.0,
    topn: int = 25,
) -> dict[str, list[dict[str, float]]]:
    expansions: dict[str, list[dict[str, float]]] = {normalize(seed): [] for seed in seeds}
    if input_path is None:
        return expansions

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    # Supported shape:
    # {"synagoge": [{"term": "moske", "score": 0.61}, ...], "moske": ["kirke", ...]}
    if not isinstance(payload, dict):
        raise ValueError("--w2v-input must contain a JSON object keyed by seed term.")

    for seed in seeds:
        seed_norm = normalize(seed)
        raw_terms = payload.get(seed_norm, payload.get(seed, []))
        if not isinstance(raw_terms, list):
            continue

        candidates: list[dict[str, float]] = []
        for item in raw_terms:
            if isinstance(item, str):
                term = normalize(item)
                score = 1.0
            elif isinstance(item, dict):
                if "term" not in item:
                    continue
                term = normalize(str(item["term"]))
                score = float(item.get("score", 1.0))
            else:
                continue

            if score < min_similarity:
                continue
            if vocab_filter is not None and term not in vocab_filter:
                continue
            candidates.append({"term": term, "score": score})

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:topn]
        expansions[seed_norm] = candidates

    return expansions


def build_coordination_graph(texts: list[str]) -> dict[str, Counter[str]]:
    graph: dict[str, Counter[str]] = defaultdict(Counter)
    for text in texts:
        for left, _, right in COORD_RE.findall(text):
            left_norm = normalize(left)
            right_norm = normalize(right)
            if left_norm == right_norm:
                continue
            graph[left_norm][right_norm] += 1
            graph[right_norm][left_norm] += 1
    return graph


def expand_with_coordination(
    seeds: list[str],
    graph: dict[str, Counter[str]],
    topn: int,
    min_edge_weight: int,
) -> dict[str, list[dict[str, int]]]:
    expansions: dict[str, list[dict[str, int]]] = {}
    for seed in seeds:
        seed_norm = normalize(seed)
        neighbors = [
            {"term": neighbor, "weight": int(weight)}
            for neighbor, weight in graph.get(seed_norm, {}).most_common(topn)
            if weight >= min_edge_weight
        ]
        expansions[seed_norm] = neighbors
    return expansions


def merge_terms(
    seeds: list[str],
    w2v_expansion: dict[str, list[dict[str, float]]],
    coord_expansion: dict[str, list[dict[str, int]]],
) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for seed in seeds:
        seed_norm = normalize(seed)
        terms = {seed_norm}
        terms.update(item["term"] for item in w2v_expansion.get(seed_norm, []))
        terms.update(item["term"] for item in coord_expansion.get(seed_norm, []))
        merged[seed_norm] = sorted(terms)
    return merged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prototype for religion-term expansion (external w2v + coordination graph)."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        required=True,
        help="Path to a .txt file or a directory with .txt files.",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        default=["moske", "moské", "synagoge", "kirke"],
        help="Seed terms for expansion.",
    )
    parser.add_argument(
        "--w2v-input",
        type=Path,
        default=None,
        help=(
            "Path to JSON with precomputed neighbors per seed. "
            "Example: {\"synagoge\": [{\"term\": \"moske\", \"score\": 0.61}]}"
        ),
    )
    parser.add_argument(
        "--w2v-topn",
        type=int,
        default=25,
        help="Top-N neighbors to keep per seed from external w2v input.",
    )
    parser.add_argument(
        "--w2v-min-sim",
        type=float,
        default=0.45,
        help="Minimum score for external w2v candidate terms.",
    )
    parser.add_argument(
        "--coord-topn",
        type=int,
        default=20,
        help="Top-N neighbors to fetch per seed from coordination graph.",
    )
    parser.add_argument(
        "--coord-min-edge",
        type=int,
        default=2,
        help="Minimum edge weight in coordination graph.",
    )
    parser.add_argument(
        "--min-freq",
        type=int,
        default=2,
        help="Minimum frequency in corpus for terms retained from w2v.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/religion_seed_expansion.json"),
        help="Where to write resulting expansion JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    texts = load_corpus_texts(args.corpus)
    vocab_filter = extract_vocab(texts, min_count=args.min_freq)

    coord_graph = build_coordination_graph(texts)
    coord_expansion = expand_with_coordination(
        seeds=args.seeds,
        graph=coord_graph,
        topn=args.coord_topn,
        min_edge_weight=args.coord_min_edge,
    )

    w2v_expansion = load_external_w2v_expansion(
        seeds=args.seeds,
        input_path=args.w2v_input,
        topn=args.w2v_topn,
        min_similarity=args.w2v_min_sim,
        vocab_filter=vocab_filter,
    )

    merged = merge_terms(
        seeds=args.seeds,
        w2v_expansion=w2v_expansion,
        coord_expansion=coord_expansion,
    )

    result = {
        "seeds": [normalize(seed) for seed in args.seeds],
        "w2v": w2v_expansion,
        "coordination": coord_expansion,
        "merged_terms": merged,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote seed expansion to {args.output}")


if __name__ == "__main__":
    main()
