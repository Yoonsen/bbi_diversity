# Luminonløype for fullt konkordanseuttrekk (DHNB 2027)

*Utkast 9.11.2026*

## Utgangspunkt

`scripts/harvest_full_concordances.py` har hentet **alle** treff for de 34 undergruppene fra abstraktet (ordlistene ligger uendret i `scripts/lexicon_dhnb2027.py`).

| | Abstrakt (utvalg) | Fullt uttrekk |
|---|---:|---:|
| Korpus (skjønn, nob, 2000–2024) | 7 012 bøker | 6 975 bøker (etter Kristins redigeringer og deduplisering) |
| Konkordansevinduer (≤ 25 ord) | 6 137 | 40 538 |
| Bøker med treff | 1 794 | se `harvest_full_summary.json` per gruppe |
| Vinduer som finnes i abstraktutvalget | | 6 128 |

Filer i `outputs/full_fiction/` (gitignorert):
- `concordances_full.jsonl`: én rad per (undergruppe, bok, vindu), med `abstract_sample_id` når vinduet var med i utvalget
- `book_word_freq.csv`: tokenfrekvens per bok × ordform (grunnlag for DF/TF og burstiness på hele korpuset)
- `harvest_full_summary.json`: tellinger og kompletthetssjekk per undergruppe

**Kompletthet:** Alle bøker som `/frequencies` finner, er representert i konkordansene (dekning 1,0 i alle grupper). Målordtokens i vinduene utgjør 89–100 % av frekvenstellingen. Avviket ligger i bøker med mange treff, og det finnes ikke noe fast tak per bok (opptil 252 vinduer i én bok). Det skyldes trolig identiske vinduer som slås sammen og forskjeller i tokenisering mellom de to endepunktene. Bør sjekkes stikkprøvevis, men er ikke en grense i API-et.

Store grupper: `kirke_bygg` 7 367, `flukt_generell` 6 217, `syn_blind` 4 388, `kristendom_identitet` 2 476, `jodedom_tora_test` 2 286. Disse fem utgjør 56 % av alle vinduer.

## Steg

### 0. Rydding før annotering
- **Utgavedubletter:** 45 tittel+forfatter-par finnes i to utgaver (f.eks. *Storm og jentungen*). Marker `dup_of` og annoter bare én av dem (abstraktet ekskluderte også utgavedubletter).
- **Identiske vinduer på tvers av bøker** (gjentatte passasjer, samleutgaver) annoteres én gang og kopieres.
- Avklar om de store gruppene skal annoteres fullt eller med et tak (for eksempel *kirke* som baseline). Anbefaling: annoter alt. Full dekning er hovedgevinsten, og kostnaden er moderat med en kompakt modell.

### 1. Fryse skjemaet (v2)
Batch 1 (`run_luminon.py`) og runde 2 (`run_luminon_round2.py`) bruker ulike sett av `litterær_funksjon`:
- runde 1: `anerkjennelse_agens / markert_annerledeshet / bakgrunnsnorm / historisk_opplysende / ikke_bokstavelig`
- runde 2: `bekreftende / problematiserende / stereotyp / bakgrunn / nøytral`

Velg ett felles sett for alle fem domener, og behold de domenespesifikke `kategori`-listene (religion 6, funksjon 5, de tre andre 5). Hver annotert rad får `schema_version`, `prompt_sha`, `model` og `run_id`, slik at kjøringer kan sammenlignes.

### 2. Annotering (kompakt modell)
- Input som før: bare opak `id`, `[domene]` og vinduet. Ingen metadata (dataminimering).
- 25 vinduer per kall, gir ca. 1 620 kall for 40 500 vinduer. Kjøringen må kunne gjenopptas: skriv fortløpende til jsonl og hopp over ID-er som allerede er ferdige.
- **Pilot først:** 3–4 små grupper (`synagoge_bygg`, `trans_kjonn`, `kven_skogfinne`, `horsel_hjelpemiddel`, ca. 700 vinduer). Sjekk etiketter og format før fullkjøringen.
- Vurder Gemini Batch-modus for de store gruppene (billigere og uten rate-limit-styr).

### 3. Regresjon mot abstraktet
De 6 128 vinduene med `abstract_sample_id` har gamle etiketter. Sammenlign gamle og nye etiketter (kappa per undergruppe). Store avvik betyr at skjemaendringen har flyttet grenser, og det må dokumenteres før tall fra abstraktet gjenbrukes.

### 4. Referansemodell og menneskelig revisjon
- Stratifisert utvalg per undergruppe × femårsperiode (for eksempel 3 per celle, ca. 500 vinduer) re-annoteres blindt med den store modellen.
- Uenigheter og lav-konfidens-tilfeller går til et revisjonsark for Kristin (CSV: id, vindu, flash-etikett, pro-etikett, tomt felt for vurdering og kommentar).
- Revisjonen kan føre til en skjemarevisjon (v3). Da kjøres bare de berørte gruppene på nytt.

### 5. Analyse på hele korpuset
- DF_w, TF_w og b_w = TF_w / DF_w per periode, nå uten utvalgsskjevhet. Nevneren er antall utgitte titler per periode (`barn.csv`).
- Kurver før og etter disambiguering (rå frekvens fra `book_word_freq.csv` mot bekreftede treff).
- Ny figur 1 og 2 på fulle data. Sammenlign med tallene i abstraktet og noter hvor de endrer seg.

## Åpne spørsmål
- Hvilket felles `litterær_funksjon`-sett skal brukes?
- Skal *kirke* og *flukt* annoteres fullt, eller med tak som baseline?
- Modellvalg: samme kompakte og store modell som i abstraktet (sammenlignbart), eller nyere?
