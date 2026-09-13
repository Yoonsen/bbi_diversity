# BBI PWA Manifest og Handover

**Til AI-assistenten i den nye økten:**
Dette dokumentet beskriver status for prosjektet og hva som skal gjøres, slik at du kan fortsette sømløst der forrige økt slapp.

## Kontekst og Mål
Vi bygger en Progressive Web App (PWA) for BBI-korpuset (Barnebokkorpuset). Appen skal gi forskere og redaktører (som Kristin) mulighet til å gjøre oppslag, søke i konkordanser, og generere trendlinjer (ordfrekvenser over tid) ved hjelp av `dhlab`. Vi bytter ut den tidligere Streamlit-tilnærmingen med en ren frontend-PWA.

## Gjeldende Status
- Vi har kombinert eldre data og nye bøker (2019-2025) til én rensket CSV-fil uten duplikater (basert på `urn`).
- Denne nye datafilen ligger nå under `data/barn.csv`.
- (Eventuell Streamlit-kode (`app.py`) som ligger igjen kan slettes/ignoreres).

## Valgt Arkitektur
- **Frontend-only (Vite + React + Tailwind):** Vi trenger ingen Python-backend. All funksjonalitet kjøres direkte i nettleseren.
- **Mal:** Vi baserer oss på strukturen fra det eksisterende `naob/pwa`-prosjektet til brukeren.
- **Metadata:** PWA-en laster inn `barn.csv` (typisk ved å parse filen lagt i `public/`-mappen eller via `data/`) for å mappe URN-er til titler, årstall, osv.
- **API (DHlab):** Siden DHlab-API-et tillater CORS, gjør vi POST-kall direkte fra React til:
  - `https://api.nb.no/dhlab/conc` (for konkordans-søk).
  - `https://api.nb.no/dhlab/frequencies` (for trendlinjer / telling av n-gram).

## Dine Oppgaver for denne økten
1. **PWA Boilerplate:** Opprett eller kopier oppsettet for en Vite/React PWA inn i mappen `pwa`.
2. **Koble Data:** Sørg for at `utils.js` (eller tilsvarende) parser `barn.csv` i stedet for `naob_metadata.csv`, og fanger opp riktige kolonner (særlig `urn`, `year`, `title`, `authors`, `kristin`).
3. **Konkordans (Fane 1):** Sett opp konkordans-søk ved å gjøre kall mot `/conc` og slå sammen resultatene med metadatakartet.
4. **Trender (Fane 2):** Lag en ny komponent som tar inn kommaseparerte ord, kaller `/frequencies` med de aktuelle URN-ene fra korpuset, aggregerer frekvensene per år, og plotter dem som trendlinjer (f.eks. med Recharts).

Start gjerne med å sjekke om `pwa/`-mappen er opprettet, og bytt til å skrive React/JS-kode!
