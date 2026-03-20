"""
Smart item classifier — maps a free-text description to the best-matching
DUTY_TYPE string (e.g. 'Cell Phones-18') and a suggested UQC.

Strategy (highest priority first):
  T1 — Exact brand / product phrase match  (e.g. 'bardinet' → Liquor-08)
  T2 — Keyword token match                 (e.g. 'whisky' → Liquor-08)
  T3 — Fallback                            → Miscellaneous-22

The map is built once at import time from BRAND_MAP + KEYWORD_MAP.
All matching is case-insensitive, on word tokens (split on space/punctuation).
"""
import re
from typing import Optional

# ── Duty type strings (must match OffenceForm.tsx DUTY_TYPES exactly) ─────────
_DT = {
    "antique":         "Antiques-01",
    "audio_cd":        "Audio CDs-02",
    "cigarette":       "Cigarettes-03",
    "currency_frn":    "Currency (Foreign)-04",
    "currency_ficn":   "Currency (FICN)-05",
    "gold_jwl":        "Gold (Jewellery)-06",
    "gold_pri":        "Gold (Primary)-07",
    "liquor":          "Liquor-08",
    "narc_ganja":      "Narcotics (Cannabis/Ganja)-09",
    "narc_heroin":     "Narcotics (Heroin/Brown Sugar)-10",
    "narc_cocaine":    "Narcotics (Cocaine)-11",
    "wildlife":        "Live Species / Wildlife-12",
    "arms":            "Arms & Ammunition-13",
    "silver":          "Silver-14",
    "stones":          "Semi Precious / Precious Stones-15",
    "video_cd":        "Video CDs-16",
    "camera":          "Cameras / Video Cameras-17",
    "cell_phone":      "Cell Phones-18",
    "cord_phone":      "Cordless Phones-19",
    "calculator":      "Calculator & Digital Diary-20",
    "electronics":     "Electronic Goods-21",
    "misc":            "Miscellaneous-22",
    "vcd_dvd":         "VCD / DVD Players-23",
    "walkman":         "Walkmans-24",
    "watch":           "Watch / Watch Movements-25",
    "textile":         "Textiles / Fabrics-26",
    "fema":            "FEMA (Foreign Exchange)-27",
    "comm_fraud_imp":  "Commercial Fraud (Imports)-28",
    "comm_fraud_exp":  "Commercial Fraud (Exports)-29",
    "tobacco":         "Tobacco / Gutkha-30",
    "morphine":        "Morphine-31",
    "opium":           "Opium-32",
    "psychotropic":    "Psychotropic Substances-33",
    "precursor":       "Ephedrine / Precursors-34",
    "ipr":             "Fake Indian Goods / IPR-35",
    "red_sanders":     "Red Sanders / Timber-36",
    "ivory":           "Ivory / Elephant Products-37",
    "pangolin":        "Pangolin / Animal Parts-38",
    "coral":           "Coral / Marine Products-39",
    "prohibited_imp":  "Prohibited Imports-40",
    "prohibited_exp":  "Prohibited Exports-41",
    "duty_evasion_imp":"Duty Evasion (Imports)-42",
    "duty_evasion_exp":"Duty Evasion (Exports)-43",
    "narc_meth":       "Narcotics (Methamphetamine/Synthetic)-52",
    "narc_ketamine":   "Narcotics (Ketamine/NPS)-53",
    "narc_mandrax":    "Narcotics (Mandrax/Methaqualone)-54",
    "narc_poppy":      "Narcotics (Other NDPS)-55",
    "narc_other":      "Narcotics (Other NDPS)-55",
    "narc_imp":        "Narcotic (Imports)-56",
    "narc_exp":        "Narcotic (Exports)-57",
    "explosives":      "Explosives-58",
    "counterfeit_curr":"Counterfeit Currency-68",
    "counterfeit_gds": "Counterfeit Goods-69",
    "other_baggage":   "Other_Baggage-99",
}

# Suggested UQC per duty key
_UQC = {
    "antique":          "NOS",
    "audio_cd":         "NOS",
    "cigarette":        "STK",
    "currency_frn":     "NOS",
    "currency_ficn":    "NOS",
    "gold_jwl":         "GMS",
    "gold_pri":         "GMS",
    "liquor":           "LTR",
    "narc_ganja":       "GMS",
    "narc_heroin":      "GMS",
    "narc_cocaine":     "GMS",
    "wildlife":         "NOS",
    "arms":             "NOS",
    "silver":           "GMS",
    "stones":           "GMS",
    "video_cd":         "NOS",
    "camera":           "NOS",
    "cell_phone":       "NOS",
    "cord_phone":       "NOS",
    "calculator":       "NOS",
    "electronics":      "NOS",
    "misc":             "NOS",
    "vcd_dvd":          "NOS",
    "walkman":          "NOS",
    "watch":            "NOS",
    "textile":          "KGS",
    "fema":             "NOS",
    "tobacco":          "GMS",
    "morphine":         "GMS",
    "opium":            "GMS",
    "psychotropic":     "GMS",
    "precursor":        "GMS",
    "ipr":              "NOS",
    "red_sanders":      "KGS",
    "ivory":            "GMS",
    "pangolin":         "GMS",
    "coral":            "GMS",
    "counterfeit_curr": "NOS",
    "counterfeit_gds":  "NOS",
    "narc_meth":        "GMS",
    "narc_ketamine":    "GMS",
    "narc_mandrax":     "GMS",
    "narc_poppy":       "KGS",
    "narc_other":       "GMS",
    "narc_imp":         "GMS",
    "narc_exp":         "GMS",
    "explosives":       "KGS",
    "other_baggage":    "NOS",
}


# ── Tier-1: Brand / product phrase map ────────────────────────────────────────
# Built from DB analysis (top items by frequency). Keys are lowercase phrases.
# Longer phrases take priority — resolved by trying longest match first.
BRAND_MAP: list[tuple[str, str]] = [
    # Liquor brands
    ("bardinet",        "liquor"),
    ("beehive",         "liquor"),
    ("chivas regal",    "liquor"),
    ("chivas",          "liquor"),
    ("johnnie walker",  "liquor"),
    ("johnny walker",   "liquor"),
    ("ballantines",     "liquor"),
    ("ballantine",      "liquor"),
    ("teachers",        "liquor"),
    ("teacher's",       "liquor"),
    ("royal stag",      "liquor"),
    ("imperial blue",   "liquor"),
    ("old monk",        "liquor"),
    ("bagpiper",        "liquor"),
    ("antiquity",       "liquor"),
    ("blenders pride",  "liquor"),
    ("blender's pride", "liquor"),
    ("jack daniels",    "liquor"),
    ("jack daniel",     "liquor"),
    ("jim beam",        "liquor"),
    ("jameson",         "liquor"),
    ("absolut",         "liquor"),
    ("smirnoff",        "liquor"),
    ("bacardi",         "liquor"),
    ("corona beer",     "liquor"),
    ("heineken",        "liquor"),
    ("tuborg",          "liquor"),
    ("kingfisher",      "liquor"),
    ("carlsberg",       "liquor"),
    ("paul john",       "liquor"),
    ("amrut",           "liquor"),
    ("kahlua",          "liquor"),
    ("baileys",         "liquor"),
    ("glen",            "liquor"),   # glenlivet, glenfiddich, etc.
    ("laphroaig",       "liquor"),
    ("macallan",        "liquor"),
    ("champagne",       "liquor"),
    ("moet",            "liquor"),
    ("hennessy",        "liquor"),
    ("martell",         "liquor"),
    ("remy martin",     "liquor"),
    ("remy",            "liquor"),
    ("courvoisier",     "liquor"),

    # Cigarette brands
    ("marlboro",        "cigarette"),
    ("dunhill",         "cigarette"),
    ("555",             "cigarette"),
    ("benson hedges",   "cigarette"),
    ("benson & hedges", "cigarette"),
    ("gudang garam",    "cigarette"),
    ("camel",           "cigarette"),
    ("winston",         "cigarette"),
    ("virginia slims",  "cigarette"),
    ("esse",            "cigarette"),
    ("gold flake",      "cigarette"),
    ("kings cigarette", "cigarette"),
    ("wills",           "cigarette"),
    ("classic cigarette","cigarette"),
    ("parliament",      "cigarette"),
    ("lucky strike",    "cigarette"),
    ("cohiba cigar",    "cigarette"),  # cigars → cigarette category
    ("havana cigar",    "cigarette"),
    ("davidoff",        "cigarette"),

    # Mobile / phone brands (always Cell Phones)
    ("iphone",          "cell_phone"),
    ("i phone",         "cell_phone"),
    ("samsung galaxy",  "cell_phone"),
    ("oneplus",         "cell_phone"),
    ("one plus",        "cell_phone"),
    ("oppo",            "cell_phone"),
    ("vivo",            "cell_phone"),
    ("nokia",           "cell_phone"),
    ("motorola",        "cell_phone"),
    ("realme",          "cell_phone"),
    ("xiaomi",          "cell_phone"),
    ("redmi",           "cell_phone"),
    ("poco",            "cell_phone"),
    ("mi phone",        "cell_phone"),
    ("huawei",          "cell_phone"),
    ("honor phone",     "cell_phone"),
    ("blackberry",      "cell_phone"),
    ("htc",             "cell_phone"),
    ("sony xperia",     "cell_phone"),
    ("pixel",           "cell_phone"),

    # Laptop / computer brands (Electronic Goods)
    ("macbook",         "electronics"),
    ("mac book",        "electronics"),
    ("macpro",          "electronics"),
    ("apple mac",       "electronics"),
    ("dell laptop",     "electronics"),
    ("hp laptop",       "electronics"),
    ("lenovo",          "electronics"),
    ("thinkpad",        "electronics"),
    ("asus laptop",     "electronics"),
    ("acer laptop",     "electronics"),
    ("toshiba laptop",  "electronics"),

    # Camera brands
    ("canon camera",    "camera"),
    ("nikon camera",    "camera"),
    ("sony camera",     "camera"),
    ("fujifilm",        "camera"),
    ("gopro",           "camera"),
    ("kodak camera",    "camera"),
    ("olympus camera",  "camera"),
    ("panasonic camera","camera"),
    ("handycam",        "camera"),
    ("handy cam",       "camera"),

    # Watch brands
    ("rolex",           "watch"),
    ("omega",           "watch"),
    ("tissot",          "watch"),
    ("seiko",           "watch"),
    ("casio",           "watch"),
    ("titan watch",     "watch"),
    ("fossil",          "watch"),
    ("rado",            "watch"),
    ("hublot",          "watch"),
    ("cartier watch",   "watch"),
    ("tag heuer",       "watch"),
    ("iwc",             "watch"),
    ("patek",           "watch"),
    ("longines",        "watch"),

    # Gold / jewellery
    ("gold ingot",      "gold_pri"),
    ("gold bar",        "gold_pri"),
    ("gold coin",       "gold_pri"),
    ("gold biscuit",    "gold_pri"),
    ("gold bit",        "gold_pri"),
    ("gold chain",      "gold_jwl"),
    ("gold necklace",   "gold_jwl"),
    ("gold bangle",     "gold_jwl"),
    ("gold ring",       "gold_jwl"),
    ("gold bracelet",   "gold_jwl"),
    ("gold earring",    "gold_jwl"),
    ("gold pendant",    "gold_jwl"),

    # Narcotics
    ("poppy seeds",     "narc_poppy"),
    ("poppy husk",      "narc_poppy"),
    ("poppy straw",     "narc_poppy"),
    ("brown sugar",     "narc_heroin"),
    ("smack",           "narc_heroin"),
    ("crack cocaine",   "narc_cocaine"),
    ("crystal meth",    "narc_meth"),
    ("mdma",            "narc_meth"),
    ("ecstasy",         "narc_meth"),
    ("lsd",             "psychotropic"),
    ("methaqualone",    "narc_mandrax"),
    ("ketamine",        "narc_ketamine"),
    ("tramadol",        "psychotropic"),
    ("diazepam",        "psychotropic"),
    ("alprazolam",      "psychotropic"),

    # Currency
    ("fake currency",    "currency_ficn"),
    ("fake note",        "currency_ficn"),
    ("fake indian currency","currency_ficn"),
    ("counterfeit note", "counterfeit_curr"),
    ("counterfeit currency","counterfeit_curr"),
    ("indian currency",  "fema"),
    ("indian rupee",     "fema"),
    ("foreign currency", "currency_frn"),
    ("usd",              "currency_frn"),
    ("us dollar",        "currency_frn"),
    ("euro",             "currency_frn"),
    ("aed",              "currency_frn"),

    # Red sanders / timber
    ("red sanders",      "red_sanders"),
    ("red sandalwood",   "red_sanders"),
    ("redwood",          "red_sanders"),

    # Precious / semi-precious stones
    ("blue sapphire",    "stones"),
    ("yellow sapphire",  "stones"),
    ("pink sapphire",    "stones"),
    ("white sapphire",   "stones"),
    ("semi precious stones", "stones"),
    ("precious stones",  "stones"),

    # Wildlife / CITES
    ("pangolin",         "pangolin"),
    ("elephant tusk",    "ivory"),
    ("ivory",            "ivory"),
    ("tortoise shell",   "coral"),
    ("sea shell",        "coral"),
    ("shark fin",        "wildlife"),
    ("shark fins",       "wildlife"),
    ("agarwood",         "wildlife"),
    ("agar wood",        "wildlife"),

    # Arms
    ("pistol",           "arms"),
    ("revolver",         "arms"),
    ("rifle",            "arms"),
    ("ammunition",       "arms"),
    ("cartridge",        "arms"),
    ("bullet",           "arms"),
    ("firearm",          "arms"),

    # Tobacco
    ("gutkha",           "tobacco"),
    ("pan masala",       "tobacco"),
    ("zarda",            "tobacco"),
    ("khaini",           "tobacco"),
    ("smokeless tobacco","tobacco"),
]

# Sort brand map: longest key first so "gudang garam" beats "garam"
BRAND_MAP.sort(key=lambda x: len(x[0]), reverse=True)


# ── Tier-2: Keyword token map ─────────────────────────────────────────────────
# Single tokens or short phrases that strongly indicate a category.
KEYWORD_MAP: list[tuple[str, str]] = [
    # Liquor
    ("liquor",      "liquor"),
    ("whisky",      "liquor"),
    ("whiskey",     "liquor"),
    ("brandy",      "liquor"),
    ("wine",        "liquor"),
    ("beer",        "liquor"),
    ("vodka",       "liquor"),
    ("rum",         "liquor"),
    ("gin",         "liquor"),
    ("alcohol",     "liquor"),
    ("scotch",      "liquor"),
    ("bourbon",     "liquor"),
    ("cognac",      "liquor"),
    ("mead",        "liquor"),
    ("sake",        "liquor"),

    # Cigarettes / tobacco
    ("cigarette",   "cigarette"),
    ("cigarettes",  "cigarette"),
    ("cigar",       "cigarette"),
    ("cigars",      "cigarette"),
    ("bidi",        "tobacco"),
    ("gutkha",      "tobacco"),
    ("tobacco",     "tobacco"),

    # Gold
    ("gold",        "gold_pri"),    # refined below: jewellery keywords override
    ("ingot",       "gold_pri"),

    # Silver
    ("silver",      "silver"),

    # Jewellery keywords → gold_jwl
    ("jewellery",   "gold_jwl"),
    ("jewelry",     "gold_jwl"),
    ("chain",       "gold_jwl"),
    ("necklace",    "gold_jwl"),
    ("bangle",      "gold_jwl"),
    ("bracelet",    "gold_jwl"),
    ("earring",     "gold_jwl"),
    ("pendant",     "gold_jwl"),

    # Phones
    ("phone",       "cell_phone"),
    ("mobile",      "cell_phone"),
    ("smartphone",  "cell_phone"),
    ("handset",     "cell_phone"),
    ("cellphone",   "cell_phone"),

    # Drones / UAVs
    ("drone",       "electronics"),
    ("drones",      "electronics"),
    ("uav",         "electronics"),
    ("dji",         "electronics"),
    ("quadcopter",  "electronics"),
    ("hexacopter",  "electronics"),
    ("octocopter",  "electronics"),
    ("fpv",         "electronics"),

    # Electronics
    ("laptop",      "electronics"),
    ("notebook",    "electronics"),
    ("computer",    "electronics"),
    ("tablet",      "electronics"),
    ("ipad",        "electronics"),
    ("television",  "electronics"),
    ("tv",          "electronics"),
    ("monitor",     "electronics"),
    ("printer",     "electronics"),
    ("projector",   "electronics"),
    ("hard disk",   "electronics"),
    ("harddisk",    "electronics"),
    ("pendrive",    "electronics"),
    ("memory card", "electronics"),

    # Camera
    ("camera",      "camera"),
    ("camcorder",   "camera"),
    ("webcam",      "camera"),

    # Watch
    ("watch",       "watch"),
    ("wristwatch",  "watch"),
    ("timepiece",   "watch"),

    # Narcotics
    ("ganja",       "narc_ganja"),
    ("marijuana",   "narc_ganja"),
    ("cannabis",    "narc_ganja"),
    ("weed",        "narc_ganja"),
    ("charas",      "narc_ganja"),
    ("hashish",     "narc_ganja"),
    ("heroin",      "narc_heroin"),
    ("cocaine",     "narc_cocaine"),
    ("coke",        "narc_cocaine"),
    ("opium",       "opium"),
    ("poppy",       "narc_poppy"),
    ("morphine",    "morphine"),
    ("ndps",        "narc_other"),
    ("narcotic",    "narc_imp"),
    ("meth",        "narc_meth"),
    ("amphetamine", "narc_meth"),
    ("mandrax",     "narc_mandrax"),
    ("lsd",         "psychotropic"),
    ("ecstasy",     "narc_meth"),

    # Currency
    ("currency",    "currency_frn"),
    ("dollars",     "currency_frn"),
    ("euros",       "currency_frn"),
    ("ficn",        "currency_ficn"),
    ("fake",        "currency_ficn"),   # "fake notes" context

    # Arms
    ("arms",        "arms"),
    ("weapon",      "arms"),
    ("gun",         "arms"),
    ("explosive",   "explosives"),

    # Textiles
    ("garment",     "textile"),
    ("shirt",       "textile"),
    ("saree",       "textile"),
    ("fabric",      "textile"),
    ("cloth",       "textile"),

    # Wildlife
    ("wildlife",    "wildlife"),
    ("ivory",       "ivory"),
    ("pangolin",    "pangolin"),
    ("coral",       "coral"),

    # Precious / semi-precious stones
    ("sapphire",        "stones"),
    ("ruby",            "stones"),
    ("emerald",         "stones"),
    ("diamond",         "stones"),
    ("gemstone",        "stones"),
    ("gemstones",       "stones"),
    ("topaz",           "stones"),
    ("amethyst",        "stones"),

    # Wildlife / CITES additions
    ("iguana",          "wildlife"),
    ("tarantula",       "wildlife"),
    ("turtle",          "wildlife"),
    ("tortoise",        "wildlife"),
    ("mongoose",        "wildlife"),
    ("monkey",          "wildlife"),
    ("parrot",          "wildlife"),
    ("cites",           "wildlife"),

    # Pharma / anabolic steroids
    ("steroid",         "prohibited_imp"),
    ("anabolic",        "prohibited_imp"),
    ("testosterone",    "prohibited_imp"),
    ("stanozolol",      "prohibited_imp"),
    ("primobolone",     "prohibited_imp"),
    ("testolone",       "prohibited_imp"),

    # Agricultural / food produce
    ("saffron",         "misc"),
    ("kesar",           "misc"),

    # Material objects (adhesive tape, polythene — concealment MO items)
    ("adhesive tape",   "misc"),
    ("polythene",       "misc"),

    # Audio / media
    ("audio cd",        "audio_cd"),
    ("cassette",        "audio_cd"),

    # Others
    ("antique",     "antique"),
    ("walkman",     "walkman"),
    ("dvd",         "vcd_dvd"),
    ("vcd",         "vcd_dvd"),
    ("cd player",   "vcd_dvd"),
    ("calculator",  "calculator"),
    ("diary",       "calculator"),
    ("cordless",    "cord_phone"),
]

# Sort keyword map: longest key first
KEYWORD_MAP.sort(key=lambda x: len(x[0]), reverse=True)


def _tokenise(text: str) -> str:
    """Lowercase and normalise whitespace/punctuation for matching."""
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower())


def classify(description: str) -> dict:
    """
    Returns: {duty_type: str, duty_key: str, uqc: str, confidence: 'high'|'medium'|'low'}
    Confidence:
      high   — brand/product phrase exact match (T1)
      medium — keyword token match (T2)
      low    — fallback Miscellaneous
    """
    if not description or not description.strip():
        return {"duty_type": _DT["misc"], "duty_key": "misc",
                "uqc": "NOS", "confidence": "low"}

    norm = _tokenise(description)

    # ── Tier 1: brand / phrase map ────────────────────────────────────────
    for phrase, key in BRAND_MAP:
        if phrase in norm:
            return {"duty_type": _DT[key], "duty_key": key,
                    "uqc": _UQC.get(key, "NOS"), "confidence": "high"}

    # ── Tier 2: keyword tokens ────────────────────────────────────────────
    # Score each duty_key by number of keyword hits
    scores: dict[str, int] = {}
    for kw, key in KEYWORD_MAP:
        if kw in norm:
            scores[key] = scores.get(key, 0) + 1

    if scores:
        best_key = max(scores, key=lambda k: scores[k])
        return {"duty_type": _DT[best_key], "duty_key": best_key,
                "uqc": _UQC.get(best_key, "NOS"), "confidence": "medium"}

    # ── Tier 3: fallback ──────────────────────────────────────────────────
    return {"duty_type": _DT["misc"], "duty_key": "misc",
            "uqc": "NOS", "confidence": "low"}
