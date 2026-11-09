#!/usr/bin/env python3
"""Luminon schema v2 (DRAFT) for the full DHNB 2027 extraction.

One source of truth for:
  - domain-specific `kategori` values, each with an explicit macro class
    (lived / thematic / backdrop / other) -- previously only in the figure code
  - one shared `litterær_funksjon` set across all five domains
  - per-domain system prompts (the model only sees its own domain's labels)
  - validation of model output

Run `python scripts/luminon_schema_v2.py > skjema_v2_utkast.md` to regenerate
the discussion document.
"""

import hashlib
import json

SCHEMA_VERSION = "v2.2-utkast-2026-11-09"
# v2.2: kontekstord_lemma replaces karakteristikker_fragment (single lemmatized
# context words, collocation-like); levd_praksis vs sosialt_hverdagsrom boundary
# sharpened; uten-relevans may have underkategori null.

# Cross-domain: who/what the target word is about. Motivated by Ørjasæter & Johnsen
# (2021): disabled figures were often newborn animals or adult side characters,
# and minorities were often groups ("muslimer", "innvandrere") rather than persons.
REFERENT = {
    "enkeltperson": "En bestemt karakter eller person.",
    "gruppe": "En gruppe eller et kollektiv («muslimene», «flyktninger», «samer»).",
    "dyr": "Et dyr (f.eks. kattunger født blinde, et lam).",
    "sted_gjenstand": "Et bygg, sted eller en gjenstand.",
    "abstrakt_ingen": "Begrep, tema eller ingen referent (metafor, idiom, diskurs).",
}

# Applies to "uten-relevans" in every domain.
UTEN_RELEVANS_UNDER = {
    "paratekst": ("Tittelside, kolofon, forlagsinformasjon, oversetternote, forfatterbiografi eller reklame for andre bøker.",
                  "2021-rapporten: «oversatt fra» og «trykket i Litauen» telte som forekomster"),
    "homonym_støy": ("Homonym, navn, ordspill eller OCR-støy.", "«fornavn/jente» 100 (Tora), «dyr» 70 (lam)"),
}

MACRO = {
    "lived": "Levd erfaring: ordet viser til faktisk identitet, praksis eller tilstand hos en karakter/gruppe.",
    "thematic": "Tematisk: diskurs, historie, konflikt, diskriminering eller identitetsmerking uten levd innenfra-perspektiv.",
    "backdrop": "Kulisse: minoriteten er til stede i omgivelsene (bygg, gjenstand, utseende), men ikke i fokus (ambient representation).",
    "other": "Annet: ikke-målbetydning (metafor, idiom, homonym, forbigående skade, action-flukt, støy).",
}

# kategori -> (macro, description). Order = order in prompt.
CATEGORIES = {
    "religion": {
        "levd_praksis": ("lived", "Faktisk religiøs praksis, tro, bønn, ritual eller aktiv deltakelse – også fellesskap rundt en religiøs handling og karakterer som besøker eller vil besøke bygget (f.eks. «går i moskeen hver fredag», «måltid etter bønnen», «ta meg med i moskeen», «feiret sabbat»)."),
        "identitetsmarkør": ("thematic", "Sosial, etnisk eller kulturell tilhørighet uten fokus på trosutøvelsen (f.eks. «en muslimsk jente», «han er jøde»)."),
        "romlig_kulisse": ("backdrop", "Bygning eller markør som fysisk kulisse, veimarkør eller stedsangivelse (f.eks. «gikk forbi moskeen»)."),
        "historisk_tematisk": ("thematic", "Historisk ramme (2. verdenskrig/Holocaust o.l.), konflikt, fordommer eller overordnet tematisk omtale."),
        "sekulær_høytid_utrop": ("backdrop", "Sekulær høytidsmarkering eller fast uttrykk/utrop uten religiøst innhold."),
        "uten-relevans": ("other", "Homonym (f.eks. jentenavnet «Tora», «heksesabbat»), etternavn eller OCR-støy."),
    },
    "funksjon": {
        "faktisk_funksjonsnedsettelse": ("lived", "Varig fysisk eller sensorisk funksjonsnedsettelse, eller bruk av hjelpemiddel, hos en person/karakter."),
        "tematisk_diskurs": ("thematic", "NY: Omtale av funksjonsnedsettelse som tema – holdninger, rettigheter, diskriminering, historie – uten en konkret karakter."),
        "objekt_miljø": ("backdrop", "Hjelpemiddel/gjenstand som løsrevet objekt eller kulisse uten tilknytning til en person med funksjonsnedsettelse."),
        "forbigående_skade": ("other", "Midlertidig skade eller situasjon (krykker etter beinbrudd, blendet av lys, lukkede øyne)."),
        "metaforisk": ("other", "Metaforisk, billedlig eller idiomatisk bruk («blind av raseri», «for døve ører», «lammet av skrekk»)."),
        "uten-relevans": ("other", "Homonym (dyret «et lam», lammekjøtt) eller støy."),
    },
    "kjonn_seksualitet": {
        "levd_identitet_relasjon": ("lived", "En karakters faktiske seksuelle orientering eller kjønnsidentitet, forelskelse, parforhold, å komme ut, skeivt fellesskap/Pride."),
        "skjellsord_negativ_sjargong": ("thematic", "Ordet brukes som skjellsord, erting eller nedsettende utbrudd, uten å beskrive faktisk skeiv identitet."),
        "tematisk_diskurs": ("thematic", "Generell omtale av seksualitet, kjønnsroller, rettigheter eller normer."),
        "fysisk_bokstavelig_idiom": ("other", "Ikke-skeiv fysisk eller idiomatisk betydning («et skeivt smil», «en streit fyr»)."),
        "uten-relevans": ("other", "Homonym eller urelatert («Homo sapiens», engelsk/latinsk ord, OCR-støy)."),
    },
    "nasjonale_minoriteter": {
        "levd_kultur_identitet": ("lived", "Samiske karakterer eller nasjonale minoriteter (kvener, skogfinner, rom, romani/tatere), deres kultur, språk, joik, kofte, reindrift eller familiebakgrunn."),
        "historisk_forfølgelse_konflikt": ("thematic", "Fornorsking, Alta-saken, forfølgelse/diskriminering, fordommer, rettighetskonflikter."),
        "eksotisk_kulisse_metafor": ("backdrop", "Flyktig bakgrunnsmarkør, romantiserende klisjé eller sammenligning («fri som en sigøyner»)."),
        "ordinær_gjenstand_homonym": ("other", "Hverdagslig ikke-minoritetsbetydning («kofte» som strikkejakke, «lavvo» på speidertur, «kven» = «hvem»)."),
        "uten-relevans": ("other", "Urelatert treff eller OCR-feil."),
    },
    "flerkulturell": {
        "levd_migrasjon_minoritet": ("lived", "Karakterer med innvandrer-, flyktning- eller flerkulturell bakgrunn, asylsøkere, asylmottak, krigsflukt, levd flerkulturell hverdag."),
        "rasisme_diskriminering_kritikk": ("thematic", "Eksplisitt tematisering eller kritikk av rasisme, fremmedfrykt eller diskriminering, eller rasistiske ytringer."),
        "utseende_beskrivelse": ("backdrop", "Nøytral omtale av hudfarge som fysisk trekk, uten rasisme- eller migrasjonsramme."),
        "action_spenning_flukt": ("other", "Ikke-migrasjonsrelatert flukt i spennings-, krim-, fantasy- eller hverdagsfortelling."),
        "uten-relevans": ("other", "Figurativ bruk («tiden flykter») eller urelatert."),
    },
}

# New, finer distinctions. Each underkategori nests under exactly one existing
# kategori, so v1 kategori and macro class are always recoverable (comparability).
# Candidates come from recurring keywords/justifications in the abstract runs.
# (domain, kategori) -> {underkategori: (description, evidence from v1 runs)}
UNDERKATEGORIER = {
    ("religion", "identitetsmarkør"): {
        "identitet_innenfra": ("Karakteren identifiserer seg selv eller fortelles innenfra som muslim/jøde/kristen (egen tilhørighet, familie, refleksjon).",
                               "stikkord «identitet» 183, «personlig» 12"),
        "identitet_utenfra": ("Andre merker en person/gruppe med religiøs tilhørighet (beskrivelse, kategorisering, stereotypi, konflikt).",
                              "«gruppe» 44, «konflikt» 23, «stereotypi» 15"),
        "synlig_markør": ("Identitet vist gjennom klær eller ytre tegn (hijab, kippa, kors).",
                          "«klesplagg» 38"),
        "fremmedhet_migrasjon": ("Religionen brukes som tegn på at noen er fremmed eller innvandrer (muslim = innvandrer).",
                                 "2021-rapporten: muslim og innvandrer klynger sammen; abstraktet: «Muslim» signaliserer fremmedhet"),
    },
    ("religion", "romlig_kulisse"): {
        "veimarkør_landemerke": ("Bygget brukes til orientering, stedsangivelse eller som del av bybildet.",
                                 "«veimarkør» 34, «stedsangivelse» 35, «landemerke» 10, «bybilde» 10"),
        "sosialt_hverdagsrom": ("Bygget som møtested eller ramme for sekulær hverdag (konsert, avtale utenfor, lekeplass ved siden av). Bønn, bønnerop eller deltakelse i religiøst fellesskap er levd_praksis, ikke dette.",
                                "«møtested» 24, «hverdagsliv» 15"),
    },
    ("religion", "historisk_tematisk"): {
        "historisk_ramme": ("Krig, Holocaust, forfølgelse, historiske hendelser.",
                            "«historisk» 101, «forfølgelse» 20, «krig» 10"),
        "religionssamtale": ("Samtale, undervisning eller refleksjon om religion, tekster, tro og tvil.",
                             "«religiøs_tekst» 27, «tolkning» 13, «filosofi» 10, «definisjon» 9"),
    },
    ("funksjon", "faktisk_funksjonsnedsettelse"): {
        "hjelpemiddel_i_bruk": ("Hjelpemiddelet brukes av en karakter (rullestol, høreapparat, førerhund, stokk).",
                                "«hjelpemiddel» 363"),
        "kommunikasjon": ("Tegnspråk, punktskrift eller annen tilrettelagt kommunikasjon i samhandling.",
                          "«kommunikasjon» 142"),
        "karaktertrekk_identitet": ("Funksjonsnedsettelsen som del av hvem karakteren er (selvforståelse, erfaring, andres blikk).",
                                    "«identitet» 32, «personlig» 32"),
        "dyr": ("Funksjonsnedsettelsen gjelder et dyr (f.eks. nyfødte kattunger som er blinde/døve, blind hund).",
                "2021-rapporten: funksjonsnedsatte var ofte «nyfødte dyreunger»"),
    },
    ("kjonn_seksualitet", "tematisk_diskurs"): {
        "aksept_utforskning": ("Samtaler om å akseptere, utforske eller forstå seksualitet/kjønn.",
                               "«aksept» 13, «utfordrer» 14"),
        "fordommer_normer": ("Tematisering av fordommer, normer og heteronormativitet.",
                             "«fordommer» 13"),
    },
    ("nasjonale_minoriteter", "ordinær_gjenstand_homonym"): {
        "dialekt_spørreord": ("«kven» o.l. som dialektalt/nynorsk spørreord.",
                              "«spørrepronomen/hvem» 67"),
        "generisk_gjenstand": ("Kofte, lavvo o.l. som vanlig klesplagg eller telt uten minoritetskontekst.",
                               "«kofte» 52, «lavvo» 25, «klesplagg» 25"),
    },
    ("flerkulturell", "levd_migrasjon_minoritet"): {
        "samtidig_migrasjon": ("Innvandring, flukt og asyl i samtid (etter ca. 1970).",
                               "«asylmottak» 17, «flyktninger» 72"),
        "historisk_flukt_utvandring": ("Flukt eller utvandring i historisk ramme (2. verdenskrig, utvandring til Amerika o.l.).",
                                       "«historisk» 24"),
        "migrasjon_som_samfunnstema": ("Migrasjon omtalt som samfunnsdebatt eller politikk, ikke knyttet til en karakter.",
                                       "«omtale» 46, «diskusjon» 16"),
    },
}

# Shared across all domains. Maps old values from round 1 / round 2 for comparison.
LITTERAER_FUNKSJON = {
    "agens_anerkjennelse": ("Karakter med agens, subjektivitet, innenfra-perspektiv eller gjenkjennelig hverdagsliv.",
                            ["anerkjennelse_agens", "bekreftende"]),
    "problematiserende": ("Kritisk belysning av fordommer, rasisme, skjellsord, utenforskap eller urett.",
                          ["problematiserende"]),
    "markert_annerledeshet": ("Markert som fremmed, eksotisk, stereotyp eller nedsettende framstilt – uten kritisk distanse.",
                              ["markert_annerledeshet", "stereotyp"]),
    "opplysende": ("Forklarende, historisk eller saksorientert omtale uten tydelig kritisk vinkel.",
                   ["historisk_opplysende"]),
    "bakgrunn": ("Umarkert bakgrunnsnorm, kulisse eller perifer nevning.",
                 ["bakgrunnsnorm", "bakgrunn"]),
    "ikke_aktuelt": ("Ikke målbetydning (metafor, idiom, homonym, forbigående, action-flukt). Brukes når kategorien har makroklasse «other».",
                     ["ikke_bokstavelig", "nøytral"]),
}

OUTPUT_FIELDS = {
    "id": "samme id som i input",
    "kategori": "én verdi fra domenets liste",
    "litterær_funksjon": "én verdi fra den felles listen",
    "underkategori": "én verdi fra listen under valgt kategori, eller null hvis kategorien ikke har underkategorier",
    "referent": "én verdi fra referent-listen",
    "karakteristikker_generert": "inntil 3 korte stikkord med egne ord som karakteriserer målordet i konteksten",
    "kontekstord_lemma": "inntil 3 enkeltord (substantiv, verb, adjektiv) fra fragmentet som sier noe om målordet, i grunnform/oppslagsform (f.eks. «brant» → «brenne», «synagogene» → «synagoge»); ikke målordet selv, ikke funksjonsord, ikke fraser",
    "begrunnelse": "maks 15 ord",
}


def subcategories(domain: str, kategori: str) -> dict:
    if kategori == "uten-relevans":
        return UTEN_RELEVANS_UNDER
    return UNDERKATEGORIER.get((domain, kategori), {})


def macro_of(domain: str, kategori: str) -> str | None:
    entry = CATEGORIES.get(domain, {}).get(kategori)
    return entry[0] if entry else None


def old_funksjon_to_v2(value: str) -> str | None:
    for new, (_, olds) in LITTERAER_FUNKSJON.items():
        if value in olds:
            return new
    return None


BOTTOM_UP_FIELDS = ("karakteristikker_generert", "kontekstord_lemma")


def output_fields(bottom_up: bool = True) -> dict:
    return {k: v for k, v in OUTPUT_FIELDS.items() if bottom_up or k not in BOTTOM_UP_FIELDS}


def system_prompt(domain: str, bottom_up: bool = True) -> str:
    cats = "\n".join(f'   - "{k}": {d}' for k, (_, d) in CATEGORIES[domain].items())
    funk = "\n".join(f'   - "{k}": {d}' for k, (d, _) in LITTERAER_FUNKSJON.items())
    subs = []
    for kat in CATEGORIES[domain]:
        u = subcategories(domain, kat)
        if u:
            subs.append(f'   Hvis kategori er "{kat}":')
            subs += [f'     - "{k}": {d}' for k, (d, _) in u.items()]
    subs_txt = "\n".join(subs)
    refs = "\n".join(f'   - "{k}": {d}' for k, d in REFERENT.items())
    fields = ",\n".join(f'      "{k}": <{v}>' for k, v in output_fields(bottom_up).items())
    return f"""Du annoterer korte tekstfragmenter (maks 25 ord) fra norske barne- og ungdomsbøker etter Luminon-rammeverket.
Alle fragmentene i denne forespørselen tilhører domenet [{domain}]. Målordet er markert med <b>...</b>.
Annoter hvert fragment uavhengig. Bruk konteksten før og etter, men alle felt skal gjelde selve målordet.

1. "kategori" – velg NØYAKTIG ÉN av disse (ingen andre verdier er gyldige):
{cats}

2. "litterær_funksjon" – velg NØYAKTIG ÉN av disse:
{funk}

3. "underkategori" – bare for kategoriene nedenfor; ellers null:
{subs_txt}

4. "referent" – hvem eller hva målordet handler om:
{refs}

Input-linjer har formen "<id> | <fragment>".
Svar med KUN gyldig JSON:
{{
  "items": [
    {{
{fields}
    }}
  ]
}}
"""


def prompt_sha(domain: str, bottom_up: bool = True) -> str:
    return hashlib.sha256(system_prompt(domain, bottom_up).encode("utf-8")).hexdigest()[:12]


def validate(domain: str, ann: dict) -> list[str]:
    """Return a list of problems; empty list = valid."""
    errs = []
    k = ann.get("kategori")
    f = ann.get("litterær_funksjon")
    if k not in CATEGORIES[domain]:
        errs.append(f"ugyldig kategori for {domain}: {k!r}")
    if f not in LITTERAER_FUNKSJON:
        errs.append(f"ugyldig litterær_funksjon: {f!r}")
    if k in CATEGORIES[domain] and f in LITTERAER_FUNKSJON:
        if (macro_of(domain, k) == "other") != (f == "ikke_aktuelt"):
            errs.append(f"inkonsistent: kategori {k} ({macro_of(domain, k)}) med funksjon {f}")
    if ann.get("referent") not in REFERENT:
        errs.append(f"ugyldig referent: {ann.get('referent')!r}")
    allowed = subcategories(domain, k)
    u = ann.get("underkategori")
    optional = k == "uten-relevans"
    if allowed and u not in allowed and not (optional and u in (None, "", "null")):
        errs.append(f"underkategori {u!r} passer ikke under {k}")
    if not allowed and u not in (None, "", "null"):
        errs.append(f"{k} har ingen underkategorier, fikk {u!r}")
    for key in ("karakteristikker_generert", "kontekstord_lemma"):
        if not isinstance(ann.get(key, []), list) or len(ann.get(key, [])) > 3:
            errs.append(f"{key} må være liste med maks 3")
    return errs


def clean_lemmas(values) -> list[str]:
    """Keep single lowercase words; drop phrases and empty strings.
    Multiword answers are dropped rather than rejecting the whole annotation."""
    out = []
    for v in values or []:
        v = str(v).strip().lower()
        if v and " " not in v and v not in out:
            out.append(v)
    return out[:3]


def render_markdown() -> str:
    out = [f"# Luminonskjema v2 – utkast til diskusjon\n",
           f"*Versjon `{SCHEMA_VERSION}`. Generert fra `scripts/luminon_schema_v2.py` – endringer gjøres der.*\n",
           "## Makroklasser\n",
           "Makroklassene var tidligere bare definert i figurkoden (`make_abstract_figures_v5.py`). "
           "Nå er de en del av skjemaet, og hver kategori peker på én av dem.\n",
           "| Makroklasse | Betydning |", "|---|---|"]
    out += [f"| `{k}` | {v} |" for k, v in MACRO.items()]
    out.append("\n## Kategori per domene\n")
    for dom, cats in CATEGORIES.items():
        out += [f"### {dom}\n", "| Kategori | Makro | Beskrivelse |", "|---|---|---|"]
        out += [f"| `{k}` | {m} | {d} |" for k, (m, d) in cats.items()]
        out.append("")
    out += ["## Litterær funksjon (felles for alle domener)\n",
            "| Verdi | Beskrivelse | Tidligere verdier |", "|---|---|---|"]
    out += [f"| `{k}` | {d} | {', '.join(f'`{o}`' for o in olds) or '–'} |" for k, (d, olds) in LITTERAER_FUNKSJON.items()]
    out += ["\n## Underkategorier (nye, nøstet under eksisterende kategorier)\n",
            "Hver underkategori hører til én gammel kategori. Kategori og makroklasse fra abstraktet kan derfor alltid hentes ut igjen, "
            "og de nye skillene kommer i tillegg. Kandidatene er hentet fra stikkord og begrunnelser som gikk igjen i abstraktkjøringene.\n",
            "| Domene / kategori | Underkategori | Beskrivelse | Belegg i v1 |", "|---|---|---|---|"]
    for (dom, kat), u in UNDERKATEGORIER.items():
        out += [f"| {dom} / `{kat}` | `{k}` | {d} | {ev} |" for k, (d, ev) in u.items()]
    out += [f"| alle / `uten-relevans` | `{k}` | {d} | {ev} |" for k, (d, ev) in UTEN_RELEVANS_UNDER.items()]
    out += ["\n## Referent (nytt felt, felles for alle domener)\n",
            "Hvem eller hva målordet handler om. Rapporten fra 2021 (Ørjasæter og Johnsen) fant at funksjonsnedsatte ofte var nyfødte dyr "
            "eller voksne bipersoner, og at minoriteter ofte ble omtalt som grupper. Feltet gjør det mulig å skille mellom slike tilfeller uten å endre kategoriene.\n",
            "| Verdi | Beskrivelse |", "|---|---|"]
    out += [f"| `{k}` | {d} |" for k, d in REFERENT.items()]
    out += ["""
## Sammenlignbarhet med abstraktet

Kontrollert mot de 6 137 annoteringene fra abstraktet: 6 069 (98,9 %) får nøyaktig samme makroklasse med v2-tabellen som med figurkoden. De 68 andre hadde etiketter fra feil domene, som v2-valideringen nå avviser. Alle gamle `litterær_funksjon`-verdier kan oversettes til det felles settet, bortsett fra 4 ugyldige.

## Endringer fra abstraktkjøringene

- **Ett promptoppsett per domene.** Modellen ser bare sitt eget domenes kategorier. Det skal hindre at etiketter lekker mellom domener, som skjedde i begge rundene (f.eks. `levd_praksis` på funksjonsord og `stereotyp` som kategori).
- **Felles `litterær_funksjon`.** Runde 1 og 2 hadde ulike sett. Det nye settet slår dem sammen. `opplysende` er nytt for runde 2-domenene, og `problematiserende` er nytt for runde 1-domenene.
- **`ikke_aktuelt` er låst til makroklassen `other`.** Valideringen avviser kombinasjoner som «metaforisk + agens_anerkjennelse».
- **Ny kategori `tematisk_diskurs` for funksjon.** Runde 1 ga 17 funksjonsvinduer etiketten `historisk_tematisk` selv om den ikke fantes i funksjonslisten, og figurkoden telte dem som thematic.
- **Bottom-up-stikkord for alle domener.** Runde 2 manglet `karakteristikker_*`.
- **Validering og ny forespørsel.** Ugyldige svar sendes på nytt i stedet for å bli lagret som `ukjent`.

## Åpne spørsmål

1. **Hvilken makroklasse skal `identitetsmarkør` ha?** Figuren i abstraktet regnet «en muslimsk jente» som thematic. Man kan argumentere for lived (identitet), og det flytter tallene for islam og jødedom mye.
2. **Er `sekulær_høytid_utrop` en kulisse eller annet?** Figuren regnet den som backdrop.
3. **Skal `forbigående_skade` være other?** Den er ikke funksjonsnedsettelse, men den er heller ikke et homonym.
4. **Er `problematiserende` og `markert_annerledeshet` gode nok til å skille fiksjonens kritiske distanse fra stereotypen den kritiserer?** Det er den vanskeligste grensen for en modell.
5. **Bør makroklassen også ha en egen klasse for skjellsord?** I dag regnes skjellsord som thematic, sammen med diskurs.
6. **Kan `identitet_innenfra` løse spørsmål 1?** Kategorien beholder makroklassen thematic for sammenligning med abstraktet, mens en ny analyse kan regne `identitet_innenfra` som lived.
7. **Hvilke underkategorier er verdt å beholde?** De er kandidater fra modellens egne stikkord, ikke testet. Piloten bør vise om de skilles stabilt (enighet mellom flash og pro) før de brukes i analysen.
8. **Mangler det underkategorier?** Aktuelle kandidater er `skjellsord` (mobbing eller vennlig erting?), `hudfarge_rasisme` (rasisme rettet mot en karakter eller tematisert generelt?) og samisk (by eller bygd?).
"""]
    return "\n".join(out)


if __name__ == "__main__":
    print(render_markdown())
