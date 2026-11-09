# Luminonskjema v2 – utkast til diskusjon

*Versjon `v2.1-utkast-2026-11-09`. Generert fra `scripts/luminon_schema_v2.py` – endringer gjøres der.*

## Makroklasser

Makroklassene var tidligere bare definert i figurkoden (`make_abstract_figures_v5.py`). Nå er de en del av skjemaet, og hver kategori peker på én av dem.

| Makroklasse | Betydning |
|---|---|
| `lived` | Levd erfaring: ordet viser til faktisk identitet, praksis eller tilstand hos en karakter/gruppe. |
| `thematic` | Tematisk: diskurs, historie, konflikt, diskriminering eller identitetsmerking uten levd innenfra-perspektiv. |
| `backdrop` | Kulisse: minoriteten er til stede i omgivelsene (bygg, gjenstand, utseende), men ikke i fokus (ambient representation). |
| `other` | Annet: ikke-målbetydning (metafor, idiom, homonym, forbigående skade, action-flukt, støy). |

## Kategori per domene

### religion

| Kategori | Makro | Beskrivelse |
|---|---|---|
| `levd_praksis` | lived | Faktisk religiøs praksis, tro, bønn, ritual eller aktiv deltakelse (f.eks. «går i moskeen hver fredag», «feiret sabbat»). |
| `identitetsmarkør` | thematic | Sosial, etnisk eller kulturell tilhørighet uten fokus på trosutøvelsen (f.eks. «en muslimsk jente», «han er jøde»). |
| `romlig_kulisse` | backdrop | Bygning eller markør som fysisk kulisse, veimarkør eller stedsangivelse (f.eks. «gikk forbi moskeen»). |
| `historisk_tematisk` | thematic | Historisk ramme (2. verdenskrig/Holocaust o.l.), konflikt, fordommer eller overordnet tematisk omtale. |
| `sekulær_høytid_utrop` | backdrop | Sekulær høytidsmarkering eller fast uttrykk/utrop uten religiøst innhold. |
| `uten-relevans` | other | Homonym (f.eks. jentenavnet «Tora», «heksesabbat»), etternavn eller OCR-støy. |

### funksjon

| Kategori | Makro | Beskrivelse |
|---|---|---|
| `faktisk_funksjonsnedsettelse` | lived | Varig fysisk eller sensorisk funksjonsnedsettelse, eller bruk av hjelpemiddel, hos en person/karakter. |
| `tematisk_diskurs` | thematic | NY: Omtale av funksjonsnedsettelse som tema – holdninger, rettigheter, diskriminering, historie – uten en konkret karakter. |
| `objekt_miljø` | backdrop | Hjelpemiddel/gjenstand som løsrevet objekt eller kulisse uten tilknytning til en person med funksjonsnedsettelse. |
| `forbigående_skade` | other | Midlertidig skade eller situasjon (krykker etter beinbrudd, blendet av lys, lukkede øyne). |
| `metaforisk` | other | Metaforisk, billedlig eller idiomatisk bruk («blind av raseri», «for døve ører», «lammet av skrekk»). |
| `uten-relevans` | other | Homonym (dyret «et lam», lammekjøtt) eller støy. |

### kjonn_seksualitet

| Kategori | Makro | Beskrivelse |
|---|---|---|
| `levd_identitet_relasjon` | lived | En karakters faktiske seksuelle orientering eller kjønnsidentitet, forelskelse, parforhold, å komme ut, skeivt fellesskap/Pride. |
| `skjellsord_negativ_sjargong` | thematic | Ordet brukes som skjellsord, erting eller nedsettende utbrudd, uten å beskrive faktisk skeiv identitet. |
| `tematisk_diskurs` | thematic | Generell omtale av seksualitet, kjønnsroller, rettigheter eller normer. |
| `fysisk_bokstavelig_idiom` | other | Ikke-skeiv fysisk eller idiomatisk betydning («et skeivt smil», «en streit fyr»). |
| `uten-relevans` | other | Homonym eller urelatert («Homo sapiens», engelsk/latinsk ord, OCR-støy). |

### nasjonale_minoriteter

| Kategori | Makro | Beskrivelse |
|---|---|---|
| `levd_kultur_identitet` | lived | Samiske karakterer eller nasjonale minoriteter (kvener, skogfinner, rom, romani/tatere), deres kultur, språk, joik, kofte, reindrift eller familiebakgrunn. |
| `historisk_forfølgelse_konflikt` | thematic | Fornorsking, Alta-saken, forfølgelse/diskriminering, fordommer, rettighetskonflikter. |
| `eksotisk_kulisse_metafor` | backdrop | Flyktig bakgrunnsmarkør, romantiserende klisjé eller sammenligning («fri som en sigøyner»). |
| `ordinær_gjenstand_homonym` | other | Hverdagslig ikke-minoritetsbetydning («kofte» som strikkejakke, «lavvo» på speidertur, «kven» = «hvem»). |
| `uten-relevans` | other | Urelatert treff eller OCR-feil. |

### flerkulturell

| Kategori | Makro | Beskrivelse |
|---|---|---|
| `levd_migrasjon_minoritet` | lived | Karakterer med innvandrer-, flyktning- eller flerkulturell bakgrunn, asylsøkere, asylmottak, krigsflukt, levd flerkulturell hverdag. |
| `rasisme_diskriminering_kritikk` | thematic | Eksplisitt tematisering eller kritikk av rasisme, fremmedfrykt eller diskriminering, eller rasistiske ytringer. |
| `utseende_beskrivelse` | backdrop | Nøytral omtale av hudfarge som fysisk trekk, uten rasisme- eller migrasjonsramme. |
| `action_spenning_flukt` | other | Ikke-migrasjonsrelatert flukt i spennings-, krim-, fantasy- eller hverdagsfortelling. |
| `uten-relevans` | other | Figurativ bruk («tiden flykter») eller urelatert. |

## Litterær funksjon (felles for alle domener)

| Verdi | Beskrivelse | Tidligere verdier |
|---|---|---|
| `agens_anerkjennelse` | Karakter med agens, subjektivitet, innenfra-perspektiv eller gjenkjennelig hverdagsliv. | `anerkjennelse_agens`, `bekreftende` |
| `problematiserende` | Kritisk belysning av fordommer, rasisme, skjellsord, utenforskap eller urett. | `problematiserende` |
| `markert_annerledeshet` | Markert som fremmed, eksotisk, stereotyp eller nedsettende framstilt – uten kritisk distanse. | `markert_annerledeshet`, `stereotyp` |
| `opplysende` | Forklarende, historisk eller saksorientert omtale uten tydelig kritisk vinkel. | `historisk_opplysende` |
| `bakgrunn` | Umarkert bakgrunnsnorm, kulisse eller perifer nevning. | `bakgrunnsnorm`, `bakgrunn` |
| `ikke_aktuelt` | Ikke målbetydning (metafor, idiom, homonym, forbigående, action-flukt). Brukes når kategorien har makroklasse «other». | `ikke_bokstavelig`, `nøytral` |

## Underkategorier (nye, nøstet under eksisterende kategorier)

Hver underkategori hører til én gammel kategori. Kategori og makroklasse fra abstraktet kan derfor alltid hentes ut igjen, og de nye skillene kommer i tillegg. Kandidatene er hentet fra stikkord og begrunnelser som gikk igjen i abstraktkjøringene.

| Domene / kategori | Underkategori | Beskrivelse | Belegg i v1 |
|---|---|---|---|
| religion / `identitetsmarkør` | `identitet_innenfra` | Karakteren identifiserer seg selv eller fortelles innenfra som muslim/jøde/kristen (egen tilhørighet, familie, refleksjon). | stikkord «identitet» 183, «personlig» 12 |
| religion / `identitetsmarkør` | `identitet_utenfra` | Andre merker en person/gruppe med religiøs tilhørighet (beskrivelse, kategorisering, stereotypi, konflikt). | «gruppe» 44, «konflikt» 23, «stereotypi» 15 |
| religion / `identitetsmarkør` | `synlig_markør` | Identitet vist gjennom klær eller ytre tegn (hijab, kippa, kors). | «klesplagg» 38 |
| religion / `identitetsmarkør` | `fremmedhet_migrasjon` | Religionen brukes som tegn på at noen er fremmed eller innvandrer (muslim = innvandrer). | 2021-rapporten: muslim og innvandrer klynger sammen; abstraktet: «Muslim» signaliserer fremmedhet |
| religion / `romlig_kulisse` | `veimarkør_landemerke` | Bygget brukes til orientering, stedsangivelse eller som del av bybildet. | «veimarkør» 34, «stedsangivelse» 35, «landemerke» 10, «bybilde» 10 |
| religion / `romlig_kulisse` | `sosialt_hverdagsrom` | Bygget som møtested eller ramme for hverdagsliv, uten religiøs handling (konsert, møte, lyd fra klokker/bønnerop). | «møtested» 24, «hverdagsliv» 15, «lyd» 12 |
| religion / `historisk_tematisk` | `historisk_ramme` | Krig, Holocaust, forfølgelse, historiske hendelser. | «historisk» 101, «forfølgelse» 20, «krig» 10 |
| religion / `historisk_tematisk` | `religionssamtale` | Samtale, undervisning eller refleksjon om religion, tekster, tro og tvil. | «religiøs_tekst» 27, «tolkning» 13, «filosofi» 10, «definisjon» 9 |
| funksjon / `faktisk_funksjonsnedsettelse` | `hjelpemiddel_i_bruk` | Hjelpemiddelet brukes av en karakter (rullestol, høreapparat, førerhund, stokk). | «hjelpemiddel» 363 |
| funksjon / `faktisk_funksjonsnedsettelse` | `kommunikasjon` | Tegnspråk, punktskrift eller annen tilrettelagt kommunikasjon i samhandling. | «kommunikasjon» 142 |
| funksjon / `faktisk_funksjonsnedsettelse` | `karaktertrekk_identitet` | Funksjonsnedsettelsen som del av hvem karakteren er (selvforståelse, erfaring, andres blikk). | «identitet» 32, «personlig» 32 |
| funksjon / `faktisk_funksjonsnedsettelse` | `dyr` | Funksjonsnedsettelsen gjelder et dyr (f.eks. nyfødte kattunger som er blinde/døve, blind hund). | 2021-rapporten: funksjonsnedsatte var ofte «nyfødte dyreunger» |
| kjonn_seksualitet / `tematisk_diskurs` | `aksept_utforskning` | Samtaler om å akseptere, utforske eller forstå seksualitet/kjønn. | «aksept» 13, «utfordrer» 14 |
| kjonn_seksualitet / `tematisk_diskurs` | `fordommer_normer` | Tematisering av fordommer, normer og heteronormativitet. | «fordommer» 13 |
| nasjonale_minoriteter / `ordinær_gjenstand_homonym` | `dialekt_spørreord` | «kven» o.l. som dialektalt/nynorsk spørreord. | «spørrepronomen/hvem» 67 |
| nasjonale_minoriteter / `ordinær_gjenstand_homonym` | `generisk_gjenstand` | Kofte, lavvo o.l. som vanlig klesplagg eller telt uten minoritetskontekst. | «kofte» 52, «lavvo» 25, «klesplagg» 25 |
| flerkulturell / `levd_migrasjon_minoritet` | `samtidig_migrasjon` | Innvandring, flukt og asyl i samtid (etter ca. 1970). | «asylmottak» 17, «flyktninger» 72 |
| flerkulturell / `levd_migrasjon_minoritet` | `historisk_flukt_utvandring` | Flukt eller utvandring i historisk ramme (2. verdenskrig, utvandring til Amerika o.l.). | «historisk» 24 |
| flerkulturell / `levd_migrasjon_minoritet` | `migrasjon_som_samfunnstema` | Migrasjon omtalt som samfunnsdebatt eller politikk, ikke knyttet til en karakter. | «omtale» 46, «diskusjon» 16 |
| alle / `uten-relevans` | `paratekst` | Tittelside, kolofon, forlagsinformasjon, oversetternote, forfatterbiografi eller reklame for andre bøker. | 2021-rapporten: «oversatt fra» og «trykket i Litauen» telte som forekomster |
| alle / `uten-relevans` | `homonym_støy` | Homonym, navn, ordspill eller OCR-støy. | «fornavn/jente» 100 (Tora), «dyr» 70 (lam) |

## Referent (nytt felt, felles for alle domener)

Hvem eller hva målordet handler om. Rapporten fra 2021 (Ørjasæter og Johnsen) fant at funksjonsnedsatte ofte var nyfødte dyr eller voksne bipersoner, og at minoriteter ofte ble omtalt som grupper. Feltet gjør det mulig å skille mellom slike tilfeller uten å endre kategoriene.

| Verdi | Beskrivelse |
|---|---|
| `enkeltperson` | En bestemt karakter eller person. |
| `gruppe` | En gruppe eller et kollektiv («muslimene», «flyktninger», «samer»). |
| `dyr` | Et dyr (f.eks. kattunger født blinde, et lam). |
| `sted_gjenstand` | Et bygg, sted eller en gjenstand. |
| `abstrakt_ingen` | Begrep, tema eller ingen referent (metafor, idiom, diskurs). |

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

