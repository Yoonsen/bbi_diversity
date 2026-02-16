Thursday, 12/Mar/2026 10:30am - 10:50am
ID: 192 / Session 2D: 1
Short paper (abstract) | 15-minute presentation with a 5-minute Q&A
Topics: Methodological innovations for engaging with neglected or dispersed digital content, Interdisciplinary insights into underexplored and diverse cultural materials, Advanced and inventive use of digital methods and computational approaches, Cultural studies, Ethnography and folklore, Gender and sexuality studies, Humanities computing, text, artificial intelligence and machine learning, concordancing and indexing, cultural analytics, data mining and analysis, natural language processing
Keywords: diversity, children's literature, LLMs, digital methods
Mapping Diversity in Norwegian Literature for Children and Young Adults (2000–2025)

Lars G Bagøien Johnsen1, Kristin Ørjasæter2

1National Library of Norway, Norway; 2Norwegian Institute for Children's Books

Purpose

This paper examines how cultural-policy ambitions for diversity correspond to identity representation in Norwegian children’s and young adult fiction published between 2000 and 2025.

We compare two corpora. The first is a large national corpus of Norwegian-language fiction and non-fiction for children and young people digitized by the National Library of Norway and made available through NB DH-LAB. The corpus supports frequency lists, concordance extraction, and collocation analysis (Birkenes & Johnsen 2025; Johnsen 2019).

The second is a smaller policy corpus consisting of two white papers from the Ministry of Culture: White Paper no. 10 (2011–2012), Culture, Inclusion, and Participation, and White Paper no. 18 (2020–2021), Experience, Create, Share. Art and Culture for, with, and by Children and Youth.

The policy corpus provides a normative framework for defining diversity. The fiction corpus provides empirical narrative practice. The study asks not only whether identities appear, but how they function contextually.

Method: From Markers to Luminons

Earlier analyses relied primarily on marker frequency and collocation. The present study extends this approach by introducing structured fragment-level annotation.

We use the term luminon to denote a qualified concordance fragment—a locally bounded textual configuration in which an identity marker is interpreted according to a predefined annotation schema. In methodological terms, luminons are instances of structured LLM-assisted annotation (cf. Mimno 2026).

Seed terms were drawn from demographic statistics, pedagogy, and policy language. These were expanded through collocation mining within the DH-LAB environment (Birkenes & Johnsen 2025). Concordances were then harvested around each marker.

Instead of counting lexical occurrences alone, we classify each concordance fragment according to interpretive distinctions such as:

literal vs. metaphorical

practice vs. theme

identity vs. event

backgrounded norm vs. marked identity

For example:

“Han går i synagogen” → religion as lived practice

“Burgerbutikken ligger bak synagogen” → religion as spatial reference

“Han var blind av raseri” → metaphorical

“Hun er blind og bruker stokk” → denotative disability

Few-shot calibrated prompts assist classification, and ambiguous cases trigger human review.

For each book, statistics are generated from luminons rather than raw tokens. We compute:

Presence: whether at least one qualified luminon of a given type occurs in a book

Intensity: the number of qualified luminons relative to text length

This allows quantitative comparison while filtering out metaphorical or incidental uses. Optional Louvain clustering visualizes shared qualified identities across books.

Our approach aligns with recent large-scale annotation efforts in literary studies, where LLMs are used to scale structured interpretation (Mimno 2026). However, luminons are anchored in concordance extraction and schema-driven labeling, ensuring bounded interpretation and reproducibility.

Cultural Policy as Framework

The white papers were analyzed using the same concordance workflow. We extracted definitional passages concerning “diversity,” “children,” and “youth,” and mapped how literature is positioned within policy discourse.

In 2011, literature is framed primarily as a tool for inclusion and democratization, especially for immigrant youth.
By 2021, children are positioned more explicitly as artistic actors, and diversity becomes embedded within institutional structures.

These policy formulations informed the operational dimensions applied in the fiction corpus.

FindingsCountries and Languages

Representation mirrors translation streams. Anglophone and Nordic contexts dominate. Large immigrant groups in Norway, such as Polish backgrounds, are weakly represented.

Pakistan stands out: when present, it is narratively central and frequently associated with transnational mobility and identity negotiation. Here, migration and religion luminons cluster.

Religion

Religion appears infrequently overall. Protestant Christianity typically functions as backgrounded seasonal or habitual practice. Minority religions more often appear as thematic framing (e.g., Holocaust narratives; migration contexts).

The asymmetry is functional: majority religion appears normalized, minority religion marked.

Sexuality and Gender Identity

Queer identities are explicitly labeled and narratively foregrounded, particularly in YA developmental arcs. Heterosexuality is largely inferred through unmarked romantic plots. The asymmetry lies in markedness: heterosexuality functions as default norm.

Disability and Deafness

Assistive-device markers are more reliable than base terms such as “blind” or “deaf,” which frequently occur metaphorically. Raw lexical counts therefore overestimate representation. Luminon qualification reveals comparatively sparse denotative disability.

Limitations

Certain identities (e.g., Sámi) require entity linking rather than naïve lexical markers due to linguistic ambiguity.

Illustrated books present a methodological limitation: diversity is often iconographic rather than lexical, and thus undercounted in a word-based pipeline.

Presence and intensity do not capture stance or stereotyping. A second-stage luminon schema focusing on agency and evaluative framing is under development.

Contribution

Methodologically, this study extends earlier corpus-based literary analysis within the National Library’s DH infrastructure (Johnsen 2019; Birkenes & Johnsen 2025) by integrating structured LLM-assisted fragment annotation.

Substantively, it shows that diversity in Norwegian children’s and YA fiction is present but unevenly structured. Majority identities function as background norms, while minority identities are more often explicitly marked and thematically framed. Intersectionality within single titles remains limited.

The gap between policy ambition and literary practice is patterned rather than absolute.

Bibliography
Birkenes, M. B., & Johnsen, L. G. (2025). Corpus and the Bibliography: NB DH-LAB as an Infrastructure for Text and Metadata I J.-M. Hanssen & S. Furuseth (Red.), The Hermeneutics of Bibliographic Data and Cultural Metadata. Oslo: Notabene.

Bishop, R.S. (1990). Mirrors, Windows and Sliding Glass Doors. I Perspectives. Choosing and Using Books for the Classroom 6 (3). https://scenicregional.org/wp-content/uploads/2017/08/Mirrors-Windows-and-Sliding-Glass-Doors.pdf [Lesedato 11.02.2020]

Johnsen, L. (2019). «Eldre bøker i den digitale samlingen. Et elektronisk blikk på tekster fra perioden 1650-1850». I Litterære verdensborgere. Transnasjonale perspektiver på norsk bokhistorie 1519-1850. A.M.B. Bjørkøy, R. Hemstad, A. Nøding & A.B. Rønning (Eds.). Oslo: Nasjonalbiblioteket, 2019, 190-214.

Mimno, David. 2026. Crossing the Room to Crossing the World: Character Movement Annotation at Scale. Talk presented at TEXT: Center for Contemporary Cultures of Text, Aarhus University, 28 January 2026.


White papers
Meld. St. 10 (2011-2012) Kultur, inkludering og deltaking.
Meld. St. 18 (2020-2021) Oppleve, skape, dele. Kunst og kultur for, med og av barn og unge.