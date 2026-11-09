"""Lexical subgroups used in the DHNB 2027 abstract (34 subgroups, five domains).

Copied verbatim from harvest_concordances.py (TASKS) and harvest_round2.py
(TASKS_ROUND2), without the per-group sample sizes, so that full extractions
can reuse the same word lists without triggering those scripts' network calls.
"""

LEXICON = [
    # --- RELIGION: BYGG/ROM ---
    ("religion", "moske_bygg", ["moske", "moské", "moskeen", "moskéen", "moskeer", "moskeene"]),
    ("religion", "synagoge_bygg", ["synagoge", "synagogen", "synagoger", "synagogene"]),
    ("religion", "kirke_bygg", ["kirke", "kirka", "kirken", "kirker", "kirkene"]),
    ("religion", "bedehus_bygg", ["bedehus", "bedehuset"]),
    # --- RELIGION: IDENTITET & PRAKSIS ---
    ("religion", "islam_identitet", ["muslim", "muslimen", "muslimer", "muslimene", "muslimsk", "muslimske", "islam", "islamsk", "islamske", "imam", "imamen"]),
    ("religion", "islam_markor", ["koran", "koranen", "ramadan", "hijab", "hijaben"]),
    ("religion", "jodedom_identitet", ["jøde", "jøden", "jøder", "jødene", "jødisk", "jødiske", "jødedom", "jødedommen", "rabbiner", "rabbineren"]),
    ("religion", "jodedom_markor", ["toraen", "sabbat", "sabbaten", "kippa", "kosher"]),
    ("religion", "jodedom_tora_test", ["tora"]),
    ("religion", "kristendom_identitet", ["kristen", "kristent", "kristne", "kristendom", "kristendommen"]),
    # --- FUNKSJONSNEDSETTELSE: SYN ---
    ("funksjon", "syn_blind", ["blind", "blinde"]),
    ("funksjon", "syn_svaksynt_blindhet", ["blindhet", "svaksynt", "svaksynte", "synshemmet", "synshemmede"]),
    ("funksjon", "syn_hjelpemiddel", ["blindestokk", "blindestokken", "blindeskrift", "punktskrift", "braille", "førerhund", "førerhunden", "førerhunder"]),
    # --- FUNKSJONSNEDSETTELSE: HØRSEL ---
    ("funksjon", "horsel_dov", ["døv", "døve"]),
    ("funksjon", "horsel_tunghort_mm", ["døvhet", "døvstum", "tunghørt", "tunghørte", "hørselshemmet", "hørselshemmede"]),
    ("funksjon", "horsel_hjelpemiddel", ["tegnspråk", "tegnspråket", "høreapparat", "høreapparatet"]),
    # --- FUNKSJONSNEDSETTELSE: BEVEGELSE ---
    ("funksjon", "bevegelse_lam", ["lam", "lamme"]),
    ("funksjon", "bevegelse_funksjonshemmet", ["funksjonshemmet", "funksjonshemmede", "funksjonsnedsettelse", "handikappet", "handikappede", "bevegelseshemmet", "bevegelseshemmede"]),
    ("funksjon", "bevegelse_rullestol", ["rullestol", "rullestolen", "rullestoler", "rullestolbruker", "protese", "protesen"]),
    ("funksjon", "bevegelse_krykker", ["krykker", "krykkene"]),
    # --- KJØNN OG SEKSUALITET ---
    ("kjonn_seksualitet", "homo_lesbisk_bifil", [
        "homofil", "homofile", "homoseksuell", "homoseksuelle",
        "lesbisk", "lesbiske", "bifil", "bifile",
        "homse", "homsen", "homser", "lesbe", "lesber", "pride", "lhbt", "lhbtq"]),
    ("kjonn_seksualitet", "homo_kortform", ["homo"]),
    ("kjonn_seksualitet", "skeiv_ord", ["skeiv", "skeive", "skjeiv", "skjeive"]),
    ("kjonn_seksualitet", "trans_kjonn", [
        "transperson", "transpersoner", "transkjønnet", "transkjønnede",
        "transseksuell", "transseksuelle", "transvestitt", "transvestitter",
        "ikkebinær", "kjønnsidentitet", "kjønnsbekreftende"]),
    ("kjonn_seksualitet", "hetero_cis", ["hetero", "heterofil", "heterofile", "heteroseksuell", "heteroseksuelle", "ciskjønnet"]),
    ("kjonn_seksualitet", "streit_ord", ["streit", "streite"]),
    # --- SAMISK OG NASJONALE MINORITETER ---
    ("nasjonale_minoriteter", "samisk_identitet", ["samisk", "samiske", "samer", "samen", "samene", "reindrift", "sapmi", "sápmi"]),
    ("nasjonale_minoriteter", "samisk_kultur_markor", ["joik", "joike", "joiker", "joiket", "kofte", "kofta", "kofter", "lavvo", "lavvoen"]),
    ("nasjonale_minoriteter", "kven_skogfinne", ["kven", "kvener", "kvenene", "kvensk", "kvenske", "skogfinne", "skogfinner", "skogfinsk"]),
    ("nasjonale_minoriteter", "rom_romani_tater", [
        "romfolk", "romfolket", "sigøyner", "sigøynere", "sigøynerne",
        "tater", "tatere", "taterne", "romani"]),
    # --- FLERKULTURELT MANGFOLD, MIGRASJON & RASISME ---
    ("flerkulturell", "innvandring_flerkultur", [
        "innvandrer", "innvandrere", "innvandrerne", "innvandring", "innvandringen",
        "flerkulturell", "flerkulturelle", "minoritetsspråklig", "minoritetsspråklige"]),
    ("flerkulturell", "flyktning_asyl", [
        "flyktning", "flyktninger", "flyktningene",
        "asylsøker", "asylsøkere", "asylmottak", "asylmottaket", "oppholdstillatelse"]),
    ("flerkulturell", "flukt_generell", ["flukt", "flykte", "flykter", "flyktet"]),
    ("flerkulturell", "hudfarge_rasisme", [
        "hudfarge", "hudfargen", "mørkhudet", "mørkhudede",
        "rasisme", "rasismen", "rasist", "rasister", "rasistisk", "rasistiske"]),
]


def surface_forms(word: str) -> list[str]:
    """Lowercase and capitalized forms, as in the original harvest scripts."""
    forms = [word.lower()]
    if word.capitalize() != word.lower():
        forms.append(word.capitalize())
    return forms
