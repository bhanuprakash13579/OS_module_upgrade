"""
Canonical default legal statutes used for remarks autogeneration.
Imported by:
  - app.main._seed_legal_statutes()  (runs on every startup, idempotent)
  - backend/scripts/seed_statutes.py (one-off CLI seeder, kept for dev use)
"""

DEFAULT_STATUTES = [
    {
        "keyword": "drone",
        "display_name": "Drones / Nano Drones",
        "is_prohibited": True,
        "supdt_goods_clause": "The import of drone in any form is prohibited vide DGFT Notification No. 54/2015-2020 dated 09.02.2022 read with Section 11(2)(u) of Customs Act, 1962 and the passenger was not in possession of any valid document for legal import of drone.",
        "adjn_goods_clause": "I find that the import of drone(s) by individuals other than government entities, educational institutions recognised by GoI, Government recognised R&D entities is prohibited vide DGFT Notification No. 54/2015-2020 dated 09.02.2022 read with Section 11(2)(u) of Customs Act, 1962. As the goods are prohibited in nature they cannot be allowed to be redeemed.",
        "legal_reference": "DGFT Notification No. 54/2015-2020 dated 09.02.2022, Section 11(2)(u) of Customs Act, 1962"
    },
    {
        "keyword": "e-cig",
        "display_name": "E-Cigarettes / Vapes",
        "is_prohibited": True,
        "supdt_goods_clause": "The E-Cigarettes/Vapes are absolutely prohibited for import, manufacture, sale, distribution and storage in terms of the Prohibition of Electronic Cigarettes (Production, Manufacture, Import, Export, Transport, Sale, Distribution, Storage and Advertisement) Act, 2019 read with CBIC Circular 35/2019.",
        "adjn_goods_clause": "The E-Cigarettes/Vapes are absolutely prohibited under the Prohibition of Electronic Cigarettes Act, 2019 and as the goods are prohibited in nature they cannot be allowed to be redeemed.",
        "legal_reference": "Prohibition of Electronic Cigarettes Act, 2019, CBIC Circular 35/2019"
    },
    {
        "keyword": "cigarette",
        "display_name": "Cigarettes / Tobacco Products",
        "is_prohibited": True,
        "supdt_goods_clause": "The cigarettes do not bear the mandatory pictorial health warnings as required under the Cigarettes and Other Tobacco Products (Packaging and Labeling) Amendment Rules, 2008 & COTPA 2003 and are in commercial quantity.",
        "adjn_goods_clause": "The cigarettes do not bear the mandatory pictorial health warnings as per COTPA, 2003 and the packaging rules therein, and pose a severe health hazard to the public if released for consumption. As the goods have failed to fulfil the conditions stipulated under COTPA, 2003 they are prohibited in nature.",
        "legal_reference": "COTPA 2003, Cigarettes and Other Tobacco Products (Packaging and Labeling) Amendment Rules, 2008"
    },
    {
        "keyword": "gutkha",
        "display_name": "Gutkha / Pan Masala",
        "is_prohibited": True,
        "supdt_goods_clause": "The gutkha/pan masala has failed to fulfil the conditions, procedures and guidelines stipulated under COTPA, 2003 and is also prohibited and restricted for sale under para 2.3.4 of FSSAI Regulation, 2011. Further the Govt. of Tamil Nadu vide Gazette dated 23 May 2017 has prohibited the manufacture, sale, storage etc. of such products.",
        "adjn_goods_clause": "The gutkha/pan masala has failed to fulfil the conditions stipulated under COTPA, 2003 and is prohibited for sale under FSSAI Regulation, 2011 and State Government orders. As the goods are prohibited in nature they cannot be allowed to be redeemed.",
        "legal_reference": "COTPA 2003, FSSAI Regulation 2011, Tamil Nadu Gazette dated 23 May 2017"
    },
    {
        "keyword": "gold",
        "display_name": "Gold / Jewellery",
        "is_prohibited": False,
        "supdt_goods_clause": "The gold was found concealed on the person/baggage of the passenger and was not declared to Customs as per Section 77 of the Customs Act, 1962, exceeding the bona-fide free allowance limits under the Baggage Rules, 2016.",
        "adjn_goods_clause": "The passenger attempted to smuggle the gold by concealing it, violating Section 77 of the Customs Act, 1962. The goods are dutiable and were not declared to the Customs authorities. By the said act of omission and commission the passenger has rendered the goods liable for confiscation.",
        "legal_reference": "Section 77, Customs Act 1962, Baggage Rules 2016"
    },
    {
        "keyword": "poppy",
        "display_name": "Poppy Seeds / Poppy Husk",
        "is_prohibited": True,
        "supdt_goods_clause": "The Poppy Seeds/Husk require mandatory registration/clearance from the Narcotics Commissioner as per DGFT import policies, which the passenger failed to produce.",
        "adjn_goods_clause": "The import of Poppy Seeds/Husk requires mandatory registration/clearance from the Narcotics Commissioner which the passenger failed to produce. As the goods are prohibited in nature they cannot be allowed to be redeemed.",
        "legal_reference": "DGFT Import Policy, NDPS Act"
    },
    {
        "keyword": "refurbish",
        "display_name": "Refurbished / Old Electronics",
        "is_prohibited": False,
        "supdt_goods_clause": "The goods are old/used/refurbished electronics which do not contain BIS mark and are imported in commercial quantity without mandatory BIS registration and DGFT authorization as per Notification No. 05/2015-2020 dated 07.05.2019.",
        "adjn_goods_clause": "As per DGFT Notification No. 05/2015-2020 dated 07.05.2019, the import of goods notified under the Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order, 2012 is prohibited unless registered with BIS and compliant with labelling requirements. The passenger has failed to produce any such registration.",
        "legal_reference": "DGFT Notification No. 05/2015-2020, BIS Registration Order 2012"
    },
    {
        "keyword": "currency",
        "display_name": "Indian / Foreign Currency",
        "is_prohibited": False,
        "supdt_goods_clause": "The currency exceeds the permissible limit prescribed under FEMA Notification No. 6(R)/2015-RB dated 29.12.2015 and was not declared to Customs.",
        "adjn_goods_clause": "The passenger attempted to illegally export/import currency exceeding the permissible threshold without proper declaration, violating FEMA Notification No. 6(R)/RB-2015 dated 29.12.2015.",
        "legal_reference": "FEMA Notification No. 6(R)/2015-RB dated 29.12.2015, FEMA 1999"
    },
    {
        "keyword": "liquor",
        "display_name": "Liquor / Alcoholic Beverages",
        "is_prohibited": False,
        "supdt_goods_clause": "The liquor brought by the passenger exceeds the duty-free allowance permissible under the Baggage Rules, 2016 and is in commercial quantity.",
        "adjn_goods_clause": "The liquor imported by the passenger is in excess of the permissible free allowance under the Baggage Rules, 2016 and is commercial in nature, which cannot be construed as bona-fide baggage.",
        "legal_reference": "Baggage Rules 2016, Customs Act 1962"
    },
    {
        "keyword": "toy",
        "display_name": "Toys (without BIS)",
        "is_prohibited": True,
        "supdt_goods_clause": "The Electric and Non-Electric toys do not have the mandatory BIS mark as required under the Toys (Quality Control) Order, 2020 issued by DPIIT, Ministry of Commerce and Industry.",
        "adjn_goods_clause": "The toys do not have the mandatory BIS mark as per the Toys (Quality Control) Order, 2020 issued by DPIIT, Ministry of Commerce and Industry. As the goods are prohibited in nature they cannot be allowed to be redeemed.",
        "legal_reference": "Toys (Quality Control) Order, 2020, DPIIT"
    },
    {
        "keyword": "narcotic",
        "display_name": "Narcotics / NDPS Substances",
        "is_prohibited": True,
        "supdt_goods_clause": "The substance is a controlled/prohibited narcotic under the NDPS Act, 1985 and its import is strictly prohibited.",
        "adjn_goods_clause": "The narcotic substance is prohibited under the NDPS Act, 1985. As the goods are prohibited in nature they cannot be allowed to be redeemed.",
        "legal_reference": "NDPS Act 1985, Customs Act 1962"
    },
    {
        "keyword": "generic_commercial",
        "display_name": "Generic Commercial Goods (Fallback)",
        "is_prohibited": False,
        "supdt_goods_clause": "The goods are in commercial quantity and are non-bonafide in nature under the Baggage Rules, 2016.",
        "adjn_goods_clause": "The goods imported are commercial in nature and exceed the bona-fide free allowance permissible under the Baggage Rules, 2016. The goods cannot be construed as bona-fide baggage.",
        "legal_reference": "Baggage Rules 2016, Customs Act 1962"
    },
]
