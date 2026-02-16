## BBI Diversity

Første prototype for å utvide religion-seedord med:

- `w2v`-likhet (precomputet eksternt og lest inn som JSON)
- koordinasjonsgraf (mønstre som `X og Y` / `X eller Y`)

### Kjøring

1) Installer avhengigheter:

```bash
pip install -e .
```

2) Kjør med korpusmappe:

```bash
python main.py --corpus data/corpus_txt
```

3) Kjør med både korpus og ekstern w2v-fil (`.json`):

```bash
python main.py --corpus data/corpus_txt --w2v-input data/w2v_neighbors.example.json
```

Eksempel på `w2v_neighbors.json`:

```json
{
  "synagoge": [
    {"term": "moske", "score": 0.61},
    {"term": "tempel", "score": 0.55}
  ],
  "moske": ["synagoge", "minaret"]
}
```

Du kan kopiere `data/w2v_neighbors.example.json` til en arbeidsfil og fylle den med egne w2v-kandidater.

Resultatet skrives til `outputs/religion_seed_expansion.json` (kan overstyres med `--output`).

### Viktige argumenter

- `--seeds`: seedord (default: `moske moské synagoge kirke`)
- `--w2v-input`: ekstern JSON med w2v-kandidater per seed
- `--w2v-topn`, `--w2v-min-sim`: terskler for eksterne w2v-kandidater
- `--coord-topn`, `--coord-min-edge`: terskler for koordinasjonskanter
- `--min-freq`: minimum frekvens i korpus for å beholde w2v-kandidater
