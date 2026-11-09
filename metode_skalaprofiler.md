# Skalaprofiler: blokktelling, burstiness og samforekomst over flere skalaer

*Metodenotat, utkast 9.11.2026. Tenkt som tillegg til de fire veiene i doc-to-vec.*

## Idé

De fleste likhetsmål for ord, både prikkprodukt mellom ordvektorer og PMI over et kontekstvindu, låser skalaen på forhånd. Word2vec med vindu 5 måler samforekomst på noen få ord. Dokumentvektorer måler den på hele dokumentet. Levy og Goldberg (2014) viste at skip-gram med negativ sampling i praksis faktoriserer en PMI-matrise (forskjøvet med log k) for ett fast vindu. Et prikkprodukt er derfor omtrent PMI ved én skala.

Med skalaprofiler blir skalaen en variabel. Teksten deles i blokker av størrelse *s*, og vi teller blokker for flere verdier av *s*. Da blir et mål på et ord, eller på et ordpar, en **kurve over s** og ikke ett tall. To ord kan ha samme prikkprodukt, men helt ulike profiler:

- **Scenisk samforekomst:** ordene står tett sammen lokalt, men er uavhengige på boknivå.
- **Tematisk samforekomst:** ordene er uavhengige lokalt, men følger hverandre på boknivå.

Fremgangsmåten minner om bokstelling (box counting) i fraktalanalyse (Mandelbrot 1982). Det som telles, er hvor mange bokser (blokker) som inneholder ordet, og hvordan dette tallet endrer seg med boksstørrelsen.

## Forløper: vindusutvidelse og avstand (Johnsen 2021)

Johnsen (2021) foreslår to lokale mål for kollokasjon som ikke trenger et globalt referansekorpus. Begge kan leses som spesialtilfeller av en skalaprofil.

**Δ-score.** PMI uten logaritme, Δ(x,y) = p(x|y) / p(x). Den er likelihood-faktoren i Bayes' formel, slik at x er relevant for y når p(x) ≠ p(x|y) (Jaynes 2003). PPMI_s nedenfor er log Δ ved skala *s*, så den bayesianske tolkningen gjelder på hver skala.

**Vindusutvidelse.** Et kollokasjonsvindu C(y) sammenlignes med et større vindu U(y) ⊃ C(y), hentet fra de samme konkordansene:

  ratio(x,y) = p(x|C(y)) / p(x|U(y))

Ord uten tilknytning til målordet øker omtrent i takt med vinduet, og forholdet blir nær 1. Ord som er bundet til målordet, er allerede fanget opp nær det og øker mindre. Dette er en **skalaprofil med to punkter**: forholdet er stigningstallet mellom to skalaer. Med mange skalaer blir den til en kurve, og formen på kurven kan tolkes.

**Lokal referanse.** Referansen U konstrueres fra kilden til kollokasjonen selv. Diskusjonen i artikkelen foreslår også å bruke tilfeldige ordsekvenser fra de samme dokumentene som nevner. Det er samme tanke som varianten *innad i bok* nedenfor, der blokker fra samme bok utgjør bakgrunnen.

**Avstand.** Gjennomsnittlig posisjon for x i vinduet rundt y, sammenlignet med midtpunktet i vinduet (forventningen for ord uten tilknytning). Gjennomsnittsavstanden er første moment av fordelingen av x etter avstand til y. Skalaprofilen er den kumulative fordelingen av den samme fordelingen. Artikkelen peker på en skjult premiss: at relevans avtar lineært med avstand, noe oblike objekter bryter med. Når hele profilen brukes i stedet for gjennomsnittet, trengs ikke den premissen. En topp ved 2–3 ord blir synlig.

**Hva som legges til.** Johnsen (2021) arbeider med vinduer *sentrert på målordet*, med retning (venstre eller høyre kontekst). Det er kollokasjon. Blokkene her er en inndeling *uten sentrum*. Det er dispersjon og tema. Skalaprofilen legger begge på samme akse: sentrert vindu (≈ 10–50 ord), blokk (250), sammenslåtte blokker og bok. Dermed får vi en sammenhengende overgang fra kollokasjon til tema. Jaccard-kurvene artikkelen bruker for å sammenligne rangeringer, kan brukes direkte til å måle hvor raskt topplisten endrer seg med *s*.

## Tre mål

La *B_s* være mengden blokker av størrelse *s* (i ord), og la *k_b(w)* være antall forekomster av ordet *w* i blokk *b*.

### 1. Dekning: hvor stor del av teksten ordet når

  f_s(w) = |{b ∈ B_s : k_b(w) > 0}| / |B_s|

Hvis forekomstene er uavhengige med rate *p* per løpeord (Poisson), er forventningen f_s ≈ 1 − e^{−ps}. Forholdet

  C_s(w) = f_s(w) / (1 − e^{−ps})

måler klumping. C_s ≈ 1 betyr at ordet er jevnt spredt. C_s < 1 betyr at ordet klumper seg, altså forekommer i færre blokker enn frekvensen tilsier. Dette er det samme fenomenet som Katz (1996) og Church og Gale (1995) beskriver som at ord «tilpasser seg» (adaptation): har et innholdsord først dukket opp, er det sannsynlig at det kommer igjen.

**Dette måler:** hvor mye ordet er bundet til tema. Det sier ingenting om hvilket tema.

### 2. Variasjon: burstiness og skalering

  F(s) = Var(k_b) / E(k_b)   (Fano-faktor ved skala *s*)

F(s) = 1 for en Poisson-prosess. Hvis F(s) vokser som s^α, er fordelingen skalainvariant (fraktal). Eksponenten α henger sammen med Hurst-eksponenten H (α ≈ 2H − 1) og måler langtrekkende korrelasjon (Lowen og Teich 2005). Allan-faktoren (Allan 1966)

  A(s) = E[(k_{i+1} − k_i)²] / (2 E[k])

gir det samme, men er mindre følsom for langsomme trender gjennom boka. Fremgangsmåten for ord i litterær tekst er beskrevet av Ebeling og Pöschel (1994), Ortuño mfl. (2002) og Altmann, Pierrehumbert og Motter (2009). Montemurro og Zanette (2010) deler teksten i blokker av varierende størrelse og finner at informasjonen ordfordelingen bærer, har et maksimum ved en karakteristisk skala.

**Dette måler:** om ordet forekommer i utbrudd, og på hvilken skala utbruddene ligger. Det kan være en scene, et kapittel eller en hel bok.

### 3. Samforekomst: PPMI som funksjon av skala

For et kandidatord *w* og en mengde markører *M*:

  PPMI_s(w, M) = max(0, log₂ [ P(w ∈ b | b ∩ M ≠ ∅) / P(w ∈ b) ])   over b ∈ B_s

Assosiasjonsmålet er det klassiske PMI (Church og Hanks 1990), med positiv avkapping (Bullinaria og Levy 2007). Det nye er bare at *s* varierer. Bakgrunnen P(w ∈ b) kan defineres på to måter:

- **Utvalg:** alle blokker i levd-bøker og referansebøker. Dette er det som er implementert i dag.
- **Innad i bok:** markørblokker mot de andre blokkene i *samme* bok. Da holdes forfatter, stil og bokas tema konstant, og målet isolerer den lokale konteksten.

**Dette måler:** hvor nært kandidatordet står markøren, og om det er nærhet i scenen (PPMI faller raskt med *s*) eller i temaet (PPMI holder seg til boknivå).

## Skalaer som allerede er tilgjengelige i bbi_diversity

| Skala | Omtrent | Kilde |
|---|---|---|
| Konkordansevindu | 50 ord (25 + 25) | `outputs/full_fiction/concordances_full.jsonl` |
| Blokk | 250 ord | DHLAB `/chunks`, lagret per bok |
| Sammenslåtte blokker | 500, 1 000, 2 000 ord | slås sammen fra 250-blokkene |
| Bok | hele teksten | `book_word_freq.csv`, bokkontrasten (`book_z`) |

Blokkene kan bare slås sammen oppover. Skalaer under 250 ord krever konkordansevinduene eller ny henting.

## Forhold til metodene vi bruker i dag

| Mål i `scripts/expand_markers.py` | Tilsvarer |
|---|---|
| `chunk_ppmi` | PPMI_s med s = 250 og utvalg som bakgrunn |
| `fano_med` | F(s) med s = 250, median over levd-bøker |
| `book_z` | Bokskala, log-odds med informativ prior (Monroe, Colaresi og Quinn 2008) |
| `galakse` | Louvain-klynger (Blondel mfl. 2008) i samforekomstgrafen ved s = 250 |
| b_w = TF/DF | Katz' (1996) mål på burstiness på bokskala |

Skalaprofilene bygger altså ikke en ny pipeline. De binder sammen målene vi allerede har, og fyller inn skalaene mellom dem. Hver blokk er også et «dokument» i LDA-forstand (Blei, Ng og Jordan 2003), så den samme inndelingen kan brukes til tematisk modellering.

## Hva vi kan teste

- **Kandidatmarkører:** skiller profilen gode markører (høy andel levd) fra ord med vanlig, overført bruk som «halt», «stum» og «synet»? Vi forventer at overført bruk er jevnere spredt (C_s nærmere 1) og har en flatere PPMI-profil.
- **H2, burstiness som filter for framstilling:** har identitet som er *levd*, en annen skaleringsprofil (α, maksimum i PPMI_s) enn identitet som bare er *kulisse*?
- **Doc-to-vec:** profiler for ordpar som et tillegg til vektorlikhet. Profilene er også et grunnlag for å velge kontekstvindu og dokumentstørrelse bevisst, i stedet for etter konvensjon.

## Forbehold

- Små *s* gir støy for sjeldne ord. Vi trenger en minstegrense for antall forekomster per skala.
- Grensene mellom blokkene følger ikke kapitler eller scener. En glidende variant (overlappende vinduer) er dyrere, men fjerner effekten av hvor grensene havner.
- Bøkene er ulikt lange, og det påvirker hvor mange blokker de har på store *s*. Vi bør vekte per bok, eller normalisere skalaen som en andel av bokas lengde.
- Fraktale eksponenter er ustabile når skalaspennet er kort. Med 50–100 000 ord har vi bare om lag tre dekader, så α bør tolkes som en trend og ikke som en presis eksponent.

## Referanser

- Allan, D. W. (1966). Statistics of atomic frequency standards. *Proceedings of the IEEE*, 54(2), 221–230.
- Altmann, E. G., Pierrehumbert, J. B., & Motter, A. E. (2009). Beyond word frequency: Bursts, lulls, and scaling in the temporal distributions of words. *PLoS ONE*, 4(11), e7678.
- Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet allocation. *Journal of Machine Learning Research*, 3, 993–1022.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, P10008.
- Bullinaria, J. A., & Levy, J. P. (2007). Extracting semantic representations from word co-occurrence statistics: A computational study. *Behavior Research Methods*, 39(3), 510–526.
- Church, K. W., & Gale, W. A. (1995). Poisson mixtures. *Natural Language Engineering*, 1(2), 163–190.
- Church, K. W., & Hanks, P. (1990). Word association norms, mutual information, and lexicography. *Computational Linguistics*, 16(1), 22–29.
- Ebeling, W., & Pöschel, T. (1994). Entropy and long-range correlations in literary English. *Europhysics Letters*, 26(4), 241–246.
- Jaynes, E. T. (2003). *Probability Theory: The Logic of Science*. Cambridge University Press.
- Johnsen, L. G. (2021). Term distance, frequency and collocations. I A. Pawłowski, J. Mačutek, S. Embleton & G. Mikros (red.), *Language and Text: Data, models, information and applications* (s. 21–36). John Benjamins. https://doi.org/10.1075/cilt.356.02joh
- Katz, S. M. (1996). Distribution of content words and phrases in text and language modelling. *Natural Language Engineering*, 2(1), 15–59.
- Levy, O., & Goldberg, Y. (2014). Neural word embedding as implicit matrix factorization. *Advances in Neural Information Processing Systems*, 27.
- Lowen, S. B., & Teich, M. C. (2005). *Fractal-Based Point Processes*. Wiley.
- Mandelbrot, B. B. (1982). *The Fractal Geometry of Nature*. W. H. Freeman.
- Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for identifying the content of political conflict. *Political Analysis*, 16(4), 372–403.
- Montemurro, M. A., & Zanette, D. H. (2010). Towards the quantification of the semantic information encoded in written language. *Advances in Complex Systems*, 13(2), 135–153.
- Ortuño, M., Carpena, P., Bernaola-Galván, P., Muñoz, E., & Somoza, A. M. (2002). Keyword detection in natural languages and DNA. *Europhysics Letters*, 57(5), 759–764.
