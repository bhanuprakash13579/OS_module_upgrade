from fastapi import APIRouter, Depends, HTTPException, Query as QParam
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func, and_, cast, Integer, extract
from collections import defaultdict
from typing import List, Optional
from datetime import date
import json
import re
from pydantic import BaseModel

from app.database import get_db
from app.models.offence import CopsMaster, CopsItems
from app.models.baggage import BrMaster, BrItems
from app.models.detention import DrMaster, DrItems
from app.services.auth import get_current_user, get_current_active_user
from app.models.auth import User


# ── Monthly Report: Tags Classifier ──────────────────────────────────────────

MONTHLY_REPORT_TAGS = [
    "Gold (Primary & Jewellery Forms)",
    "Silver",
    "Drone",
    "Foreign Currency (Equivalent to Indian Rs.)",
    "Indian Currency (Quantity in Nos.)",
    "Garments",
    "Diamonds & Precious Stones",
    "Wild Life / Flora / Fauna",
    "Ganja",
    "Fabrics",
    "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)",
    "Liquor",
    "Miscellaneous Goods (With Different Unit Qty Codes)",
    "E-CIGARETTES",
    "Cigarettes",
    "Poppy Seeds",
    "Heroin",
    "Cocaine",
    "Morphine",
    "Hashish / Charas",
    "Mandrax / Methaqualone",
    "Opium",
    "Acetic_Anhydride",
    "Misc. Electronic Items (CDs,DVDs,Walkman,Calculator,Digital Diary etc)",
    "Other Narcotics",
    "Antiquities",
    "Watches",
    "Watch_Parts",
    "Zip Fasteners",
    "Synthetic Fibre / Yarn Waste",
    "Pharmaceutical Drugs / Medicines",
    "Chemicals",
    "Computer And Computer Parts",
    "Ball Bearings",
    "Machinery And Parts Thereof",
    "Indian Fake Currency Notes (FICN)- Face Value in Rs.",
    "Agricultural Produce",
    "Vehicles",
    "Vessels",
    "Aircrafts",
    "Arms & Ammunition",
    "Explosives",
    "Red Sanders (Qty in MTS)",
    "Metal Scrap",
    "Ozone Depleting Substances Like R-22 Gas Etc",
    "Ketamine",
]

# Keyword → tag mapping (longest phrase first for priority)
_TAG_KW_MAP: list[tuple[str, str]] = sorted([
    ("acetic anhydride",    "Acetic_Anhydride"),
    ("precursor",           "Acetic_Anhydride"),
    ("ephedrine",           "Acetic_Anhydride"),
    ("drone",               "Drone"),
    ("quadcopter",          "Drone"),
    ("hexacopter",          "Drone"),
    ("octocopter",          "Drone"),
    ("uav drone",           "Drone"),
    ("dji",                 "Drone"),
    ("r-22 gas",            "Ozone Depleting Substances Like R-22 Gas Etc"),
    ("r-22",                "Ozone Depleting Substances Like R-22 Gas Etc"),
    ("refrigerant gas",     "Ozone Depleting Substances Like R-22 Gas Etc"),
    ("ozone",               "Ozone Depleting Substances Like R-22 Gas Etc"),
    ("metal scrap",         "Metal Scrap"),
    ("scrap metal",         "Metal Scrap"),
    ("iron scrap",          "Metal Scrap"),
    ("copper scrap",        "Metal Scrap"),
    ("ball bearing",        "Ball Bearings"),
    ("machinery part",      "Machinery And Parts Thereof"),
    ("machine part",        "Machinery And Parts Thereof"),
    ("machine parts",       "Machinery And Parts Thereof"),
    ("machinery",           "Machinery And Parts Thereof"),
    ("computer part",       "Computer And Computer Parts"),
    ("computer parts",      "Computer And Computer Parts"),
    ("laptop",              "Computer And Computer Parts"),
    ("notebook computer",   "Computer And Computer Parts"),
    ("server",              "Computer And Computer Parts"),
    ("zip fastener",        "Zip Fasteners"),
    ("zipper",              "Zip Fasteners"),
    ("synthetic fibre",     "Synthetic Fibre / Yarn Waste"),
    ("synthetic fiber",     "Synthetic Fibre / Yarn Waste"),
    ("yarn waste",          "Synthetic Fibre / Yarn Waste"),
    ("yarn",                "Synthetic Fibre / Yarn Waste"),
    ("synthetic yarn",      "Synthetic Fibre / Yarn Waste"),
    ("watch part",          "Watch_Parts"),
    ("watch movement",      "Watch_Parts"),
    ("watch parts",         "Watch_Parts"),
    ("watch movements",     "Watch_Parts"),
    ("electronic cigarette","E-CIGARETTES"),
    ("e-cigarette",         "E-CIGARETTES"),
    ("e cigarette",         "E-CIGARETTES"),
    ("vaping device",       "E-CIGARETTES"),
    ("vape",                "E-CIGARETTES"),
    ("juul",                "E-CIGARETTES"),
    ("iqos",                "E-CIGARETTES"),
    ("indian currency",     "Indian Currency (Quantity in Nos.)"),
    ("indian rupee",        "Indian Currency (Quantity in Nos.)"),
    ("indian note",         "Indian Currency (Quantity in Nos.)"),
    ("foreign currency",    "Foreign Currency (Equivalent to Indian Rs.)"),
    ("foreign exchange",    "Foreign Currency (Equivalent to Indian Rs.)"),
    ("ficn",                "Indian Fake Currency Notes (FICN)- Face Value in Rs."),
    ("counterfeit note",    "Indian Fake Currency Notes (FICN)- Face Value in Rs."),
    ("fake note",           "Indian Fake Currency Notes (FICN)- Face Value in Rs."),
    ("fake currency",       "Indian Fake Currency Notes (FICN)- Face Value in Rs."),
    ("forged note",         "Indian Fake Currency Notes (FICN)- Face Value in Rs."),
    ("gold",                "Gold (Primary & Jewellery Forms)"),
    ("silver",              "Silver"),
    ("diamond",             "Diamonds & Precious Stones"),
    ("precious stone",      "Diamonds & Precious Stones"),
    ("sapphire",            "Diamonds & Precious Stones"),
    ("ruby",                "Diamonds & Precious Stones"),
    ("emerald",             "Diamonds & Precious Stones"),
    ("gemstone",            "Diamonds & Precious Stones"),
    ("coral",               "Wild Life / Flora / Fauna"),
    ("ivory",               "Wild Life / Flora / Fauna"),
    ("pangolin",            "Wild Life / Flora / Fauna"),
    ("elephant tusk",       "Wild Life / Flora / Fauna"),
    ("wildlife",            "Wild Life / Flora / Fauna"),
    ("ganja",               "Ganja"),
    ("marijuana",           "Ganja"),
    ("cannabis",            "Ganja"),
    ("poppy seed",          "Poppy Seeds"),
    ("poppy husk",          "Poppy Seeds"),
    ("poppy straw",         "Poppy Seeds"),
    ("poppy",               "Poppy Seeds"),
    ("heroin",              "Heroin"),
    ("brown sugar",         "Heroin"),
    ("cocaine",             "Cocaine"),
    ("morphine",            "Morphine"),
    ("opium",               "Opium"),
    ("hashish",             "Hashish / Charas"),
    ("charas",              "Hashish / Charas"),
    ("mandrax",             "Mandrax / Methaqualone"),
    ("methaqualone",        "Mandrax / Methaqualone"),
    ("ketamine",            "Ketamine"),
    ("pharmaceutical",      "Pharmaceutical Drugs / Medicines"),
    ("medicine",            "Pharmaceutical Drugs / Medicines"),
    ("steroid",             "Pharmaceutical Drugs / Medicines"),
    ("psychotropic",        "Pharmaceutical Drugs / Medicines"),
    ("chemical",            "Chemicals"),
    ("liquor",              "Liquor"),
    ("whisky",              "Liquor"),
    ("whiskey",             "Liquor"),
    ("brandy",              "Liquor"),
    ("wine",                "Liquor"),
    ("vodka",               "Liquor"),
    ("rum",                 "Liquor"),
    ("beer",                "Liquor"),
    ("alcohol",             "Liquor"),
    ("scotch",              "Liquor"),
    ("champagne",           "Liquor"),
    ("cigarette",           "Cigarettes"),
    ("cigar",               "Cigarettes"),
    ("garment",             "Garments"),
    ("shirt",               "Garments"),
    ("trouser",             "Garments"),
    ("pant",                "Garments"),
    ("dress",               "Garments"),
    ("saree",               "Garments"),
    ("lehenga",             "Garments"),
    ("clothes",             "Garments"),
    ("fabric",              "Fabrics"),
    ("textile",             "Fabrics"),
    ("cloth",               "Fabrics"),
    ("cell phone",          "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("mobile phone",        "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("smartphone",          "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("iphone",              "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("camera",              "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("television",          "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("dvd player",          "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("electronic",          "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("mobile",              "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("samsung",             "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("android phone",       "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("ipad",                "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("android tablet",      "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("headphone",           "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("earphone",            "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("airpod",              "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("power bank",          "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("smartwatch",          "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("fitness band",        "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"),
    ("walkman",             "Misc. Electronic Items (CDs,DVDs,Walkman,Calculator,Digital Diary etc)"),
    ("calculator",          "Misc. Electronic Items (CDs,DVDs,Walkman,Calculator,Digital Diary etc)"),
    ("digital diary",       "Misc. Electronic Items (CDs,DVDs,Walkman,Calculator,Digital Diary etc)"),
    ("audio cd",            "Misc. Electronic Items (CDs,DVDs,Walkman,Calculator,Digital Diary etc)"),
    ("dvd",                 "Misc. Electronic Items (CDs,DVDs,Walkman,Calculator,Digital Diary etc)"),
    ("watch",               "Watches"),
    ("wristwatch",          "Watches"),
    ("rolex",               "Watches"),
    ("omega watch",         "Watches"),
    ("gold jewellery",      "Gold (Primary & Jewellery Forms)"),
    ("gold jewelry",        "Gold (Primary & Jewellery Forms)"),
    ("gold bangle",         "Gold (Primary & Jewellery Forms)"),
    ("gold chain",          "Gold (Primary & Jewellery Forms)"),
    ("gold necklace",       "Gold (Primary & Jewellery Forms)"),
    ("gold ring",           "Gold (Primary & Jewellery Forms)"),
    ("gold bracelet",       "Gold (Primary & Jewellery Forms)"),
    ("gold earring",        "Gold (Primary & Jewellery Forms)"),
    ("gold pendant",        "Gold (Primary & Jewellery Forms)"),
    ("gold coin",           "Gold (Primary & Jewellery Forms)"),
    ("gold bar",            "Gold (Primary & Jewellery Forms)"),
    ("gold biscuit",        "Gold (Primary & Jewellery Forms)"),
    ("yellow metal",        "Gold (Primary & Jewellery Forms)"),
    ("silver jewellery",    "Silver"),
    ("silver ornament",     "Silver"),
    ("silver coin",         "Silver"),
    ("diamond",             "Diamonds & Precious Stones"),
    ("gemstone",            "Diamonds & Precious Stones"),
    ("ruby",                "Diamonds & Precious Stones"),
    ("emerald",             "Diamonds & Precious Stones"),
    ("sapphire",            "Diamonds & Precious Stones"),
    ("pearl",               "Diamonds & Precious Stones"),
    ("precious stone",      "Diamonds & Precious Stones"),
    ("semi precious",       "Diamonds & Precious Stones"),
    ("pharmaceutical",      "Pharmaceutical Drugs / Medicines"),
    ("medicine",            "Pharmaceutical Drugs / Medicines"),
    ("capsule",             "Pharmaceutical Drugs / Medicines"),
    ("injection",           "Pharmaceutical Drugs / Medicines"),
    ("steroid",             "Pharmaceutical Drugs / Medicines"),
    ("antique",             "Antiquities"),
    ("antiquity",           "Antiquities"),
    ("red sanders",         "Red Sanders (Qty in MTS)"),
    ("red sandalwood",      "Red Sanders (Qty in MTS)"),
    ("aircraft",            "Aircrafts"),
    ("airplane",            "Aircrafts"),
    ("vessel",              "Vessels"),
    ("boat",                "Vessels"),
    ("vehicle",             "Vehicles"),
    ("car",                 "Vehicles"),
    ("motorcycle",          "Vehicles"),
    ("arms",                "Arms & Ammunition"),
    ("ammunition",          "Arms & Ammunition"),
    ("gun",                 "Arms & Ammunition"),
    ("pistol",              "Arms & Ammunition"),
    ("explosive",           "Explosives"),
    ("agricultural",        "Agricultural Produce"),
    ("saffron",             "Agricultural Produce"),
    ("currency",            "Foreign Currency (Equivalent to Indian Rs.)"),
], key=lambda x: len(x[0]), reverse=True)


def _tag_from_duty_type(duty_type_str: str) -> str:
    """Map a stored duty_type string (e.g. 'Cell Phones-18') to a report tag."""
    if not duty_type_str:
        return "Miscellaneous Goods (With Different Unit Qty Codes)"
    dt = duty_type_str.lower()
    if "gold" in dt:
        return "Gold (Primary & Jewellery Forms)"
    if "silver" in dt:
        return "Silver"
    if "liquor" in dt:
        return "Liquor"
    if "cigarette" in dt:
        # e-cigarette check
        if "e-cig" in dt or "electronic cig" in dt:
            return "E-CIGARETTES"
        return "Cigarettes"
    if any(x in dt for x in ["cell phone", "mobile phone", "smartphone", "iphone", "camera", "television", "cordless phone", "electronic good", "vcd", "dvd player", "tablet", "ipad", "headphone", "power bank", "smartwatch"]):
        return "Consumer Electronics (Cameras,Televisions,Cell Phones,DVD Players Etc)"
    if any(x in dt for x in ["walkman", "calculator", "diary", "audio cd", "video cd"]):
        return "Misc. Electronic Items (CDs,DVDs,Walkman,Calculator,Digital Diary etc)"
    if "watch movement" in dt or "watch part" in dt:
        return "Watch_Parts"
    if "watch" in dt:
        return "Watches"
    if "ganja" in dt or "cannabis" in dt:
        return "Ganja"
    if "heroin" in dt or "brown sugar" in dt:
        return "Heroin"
    if "cocaine" in dt:
        return "Cocaine"
    if "morphine" in dt:
        return "Morphine"
    if "opium" in dt:
        return "Opium"
    if "hashish" in dt or "charas" in dt:
        return "Hashish / Charas"
    if "mandrax" in dt or "methaqualone" in dt:
        return "Mandrax / Methaqualone"
    if "ketamine" in dt:
        return "Ketamine"
    if "poppy" in dt:
        return "Poppy Seeds"
    if "methamphetamine" in dt or "synthetic" in dt:
        return "Other Narcotics"
    if "narcotic" in dt or "ndps" in dt:
        return "Other Narcotics"
    if "psychotropic" in dt or "precursor" in dt or "ephedrine" in dt:
        return "Pharmaceutical Drugs / Medicines"
    if "prohibited" in dt:
        return "Pharmaceutical Drugs / Medicines"
    if "ficn" in dt or "counterfeit curr" in dt:
        return "Indian Fake Currency Notes (FICN)- Face Value in Rs."
    if "foreign currency" in dt or "fema" in dt or "foreign exchange" in dt:
        return "Foreign Currency (Equivalent to Indian Rs.)"
    if "currency" in dt:
        return "Foreign Currency (Equivalent to Indian Rs.)"
    if any(x in dt for x in ["wildlife", "ivory", "elephant", "pangolin", "coral", "live species"]):
        return "Wild Life / Flora / Fauna"
    if "arms" in dt or "ammunition" in dt:
        return "Arms & Ammunition"
    if "explosive" in dt:
        return "Explosives"
    if any(x in dt for x in ["precious stone", "sapphire", "diamond", "gemstone", "ruby", "emerald", "pearl", "semi precious"]):
        return "Diamonds & Precious Stones"
    if "red sanders" in dt or "sandalwood" in dt:
        return "Red Sanders (Qty in MTS)"
    if "textile" in dt or "fabric" in dt:
        return "Fabrics"
    if "garment" in dt:
        return "Garments"
    if "antique" in dt:
        return "Antiquities"
    if any(x in dt for x in ["medicine", "pharmaceutical", "drug", "capsule", "injection", "steroid"]):
        return "Pharmaceutical Drugs / Medicines"
    if any(x in dt for x in ["jewellery", "jewelry", "necklace", "bangle", "bracelet", "earring", "pendant", "yellow metal"]):
        return "Gold (Primary & Jewellery Forms)"
    if "chemical" in dt:
        return "Chemicals"
    return "Miscellaneous Goods (With Different Unit Qty Codes)"


def _tag_from_desc(desc: str) -> str:
    """Map a free-text description to a report tag using keyword matching."""
    if not desc:
        return "Miscellaneous Goods (With Different Unit Qty Codes)"
    norm = re.sub(r'[^a-z0-9 ]', ' ', desc.lower())
    for kw, tag in _TAG_KW_MAP:
        if kw in norm:
            return tag
    return "Miscellaneous Goods (With Different Unit Qty Codes)"


def _classify_items_tags(items: list) -> str:
    """Return comma-separated report tags for a list of CopsItems."""
    seen: list[str] = []
    seen_set: set[str] = set()
    for item in items:
        duty_type = getattr(item, 'items_duty_type', None) or ''
        desc = getattr(item, 'items_desc', None) or ''
        # Prefer duty_type classification (already vetted by SDO), fall back to desc
        tag = _tag_from_duty_type(duty_type) if duty_type else _tag_from_desc(desc)
        # Also try desc override for high-specificity items
        if tag == "Miscellaneous Goods (With Different Unit Qty Codes)" and desc:
            tag = _tag_from_desc(desc)
        if tag not in seen_set:
            seen_set.add(tag)
            seen.append(tag)
    return ", ".join(seen) if seen else ""


def _build_item_desc(items: list) -> str:
    """Build 'qty unit description' strings for all items, comma-separated."""
    parts = []
    for item in items:
        qty = item.items_qty or 0
        uqc = (item.items_uqc or '').strip()
        desc = (item.items_desc or '').strip()
        qty_str = f"{qty:g}" if qty else "0"
        parts.append(f"{qty_str} {uqc} {desc}".strip())
    return ", ".join(filter(None, parts))


def _parse_br_entries(json_str: str | None) -> tuple[str, str]:
    """Parse post_adj_br_entries JSON → (br_numbers_str, br_dates_str)."""
    if not json_str:
        return "", ""
    try:
        entries = json.loads(json_str)
        numbers = [str(e.get("no", "")).strip() for e in entries if e.get("no")]
        dates = []
        for e in entries:
            d = (e.get("date") or "").strip()
            if d:
                # Convert YYYY-MM-DD → DD-MM-YYYY
                try:
                    parts = d.split("-")
                    if len(parts) == 3 and len(parts[0]) == 4:
                        d = f"{parts[2]}-{parts[1]}-{parts[0]}"
                except Exception:
                    pass
                dates.append(d)
        return ", ".join(numbers), ", ".join(dates)
    except Exception:
        return "", ""


def _format_dr_remarks(dr_no: str | None, dr_date) -> str:
    """Format DR number + date as 'DR.No.9598 dt.05.03.2026'."""
    if not dr_no:
        return ""
    parts = [f"DR.No.{dr_no}"]
    if dr_date:
        try:
            d = str(dr_date)
            if "-" in d and len(d) >= 10:
                y, m, day = d[:10].split("-")
                parts.append(f"dt.{day}.{m}.{y}")
        except Exception:
            pass
    return " ".join(parts)


def _confiscation_label(items: list) -> str:
    """Determine confiscation label from item release categories."""
    cats: set[str] = set()
    for item in items:
        rc = (getattr(item, 'items_release_category', None) or '').upper().strip()
        if rc == 'CONFS':
            cats.add('Absolute Confiscation')
        elif rc == 'REF':
            cats.add('Re-Export')
        elif rc == 'RF':
            cats.add('Confiscation')
    if not cats:
        return ""
    return " & ".join(sorted(cats))

router = APIRouter(prefix="/api/os-query", tags=["OS Query"])

# ── Schemas ──

class OSQueryRequest(BaseModel):
    # Core identifiers
    os_no: Optional[str] = None
    os_year: Optional[int] = None
    dr_no: Optional[str] = None
    dr_year: Optional[int] = None
    
    # Dates
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    
    # Passenger info
    pax_name: Optional[str] = None
    passport_no: Optional[str] = None
    flight_no: Optional[str] = None
    
    # Flight/Route
    port_of_dep_dest: Optional[str] = None
    country_of_departure: Optional[str] = None
    
    # Values
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # Goods
    item_desc: Optional[str] = None

    # Case type filter: "Export Case" | "Arrival Case" | None (all)
    case_type: Optional[str] = None

    # Sorting
    sort_by: str = "os_year"
    sort_dir: str = "desc"

    # Pagination
    page: int = 1
    limit: int = 100

class OSQueryItemResponse(BaseModel):
    items_sno: int
    items_desc: Optional[str]
    items_qty: float
    items_uqc: Optional[str]
    items_value: float
    items_fa: float = 0.0                   # Free Allowance (value-mode)
    items_fa_type: str = 'value'            # 'value' | 'qty' — critical for FA calculation
    items_fa_qty: Optional[float] = None    # FA quantity (qty-mode)
    items_fa_uqc: Optional[str] = None      # FA unit (qty-mode)
    items_duty_type: Optional[str]
    items_release_category: Optional[str] = None   # CONFS/RF/REF — needed for print confiscation calc
    value_per_piece: float = 0.0
    cumulative_duty_rate: float = 0.0

    class Config:
        from_attributes = True

class OSQueryResponse(BaseModel):
    os_no: str
    os_year: int
    os_date: date
    pax_name: Optional[str]
    passport_no: Optional[str]
    flight_no: Optional[str]
    flight_date: Optional[date]
    total_items_value: float
    total_duty_amount: float
    total_payable: float
    adjudication_date: Optional[date]
    is_draft: str
    
    # OSPrintView Extended Fields
    booked_by: Optional[str] = None            # Used in OS No. display (e.g. "AIU 12/2026")
    os_printed: str = "N"                      # Print-lock flag read by handlePrint()
    shift: Optional[str] = None
    detention_date: Optional[date] = None
    father_name: Optional[str] = None
    pax_address1: Optional[str] = None
    pax_address2: Optional[str] = None
    pax_address3: Optional[str] = None
    passport_date: Optional[date] = None
    port_of_dep_dest: Optional[str] = None
    country_of_departure: Optional[str] = None
    pax_nationality: Optional[str] = None
    nationality: Optional[str] = None
    date_of_departure: Optional[str] = None
    stay_abroad_days: Optional[int] = None
    residence_at: Optional[str] = None
    previous_visits: Optional[str] = None
    confiscated_value: float = 0.0
    redeemed_value: float = 0.0
    re_export_value: float = 0.0
    rf_amount: float = 0.0
    ref_amount: float = 0.0
    pp_amount: float = 0.0
    supdts_remarks: Optional[str] = None
    adjn_offr_remarks: Optional[str] = None
    adj_offr_name: Optional[str] = None
    adj_offr_designation: Optional[str] = None

    # Post-adjudication metadata
    post_adj_br_entries: Optional[str] = None
    post_adj_dr_no:      Optional[str] = None
    post_adj_dr_date:    Optional[date] = None

    case_type: Optional[str] = None

    items: List[OSQueryItemResponse] = []

    class Config:
        from_attributes = True

class OSQueryPaginatedResponse(BaseModel):
    items: List[OSQueryResponse]
    total_count: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ── Endpoints ──

@router.post("/search", response_model=OSQueryPaginatedResponse)
def search_os_cases(
    query: OSQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Query Offence/Seizure records based on dynamic filters.
    Requires SDO, DC, AC, or Admin roles.
    """
    
    # Start with base query — always exclude soft-deleted master records
    if query.item_desc:
        q = db.query(CopsMaster).join(
            CopsItems, 
            and_(CopsMaster.os_no == CopsItems.os_no, CopsMaster.os_year == CopsItems.os_year)
        )
    else:
        q = db.query(CopsMaster)

    # Always exclude soft-deleted cases
    q = q.filter(CopsMaster.entry_deleted != "Y")

    # ── Identifiers ──
    if query.os_no:
        q = q.filter(CopsMaster.os_no == query.os_no)
    if query.os_year:
        q = q.filter(CopsMaster.os_year == query.os_year)
    if query.dr_no:
        q = q.filter(CopsMaster.dr_no == query.dr_no)
    if query.dr_year:
        q = q.filter(CopsMaster.dr_year == query.dr_year)

    # ── Dates ──
    if query.from_date:
        q = q.filter(CopsMaster.os_date >= query.from_date)
    if query.to_date:
        q = q.filter(CopsMaster.os_date <= query.to_date)

    # ── Passenger Info ──
    if query.pax_name:
        q = q.filter(CopsMaster.pax_name.ilike(f"%{query.pax_name}%"))
        
    if query.passport_no:
        # Check both current passport and legacy/old passport fields
        pno = query.passport_no
        q = q.filter(
            or_(
                CopsMaster.passport_no.ilike(f"%{pno}%"),
                CopsMaster.old_passport_no.ilike(f"%{pno}%")
            )
        )
        
    if query.flight_no:
        q = q.filter(CopsMaster.flight_no.ilike(f"%{query.flight_no}%"))

    # ── Route Info ──
    if query.port_of_dep_dest:
        q = q.filter(CopsMaster.port_of_dep_dest.ilike(f"%{query.port_of_dep_dest}%"))
        
    # Arrived From / Country of departure
    if query.country_of_departure:
        q = q.filter(CopsMaster.country_of_departure.ilike(f"%{query.country_of_departure}%"))

    # ── Values ──
    if query.min_value is not None:
        q = q.filter(CopsMaster.total_items_value >= query.min_value)
    if query.max_value is not None:
        q = q.filter(CopsMaster.total_items_value <= query.max_value)

    # ── Goods ──
    if query.item_desc:
        q = q.filter(CopsItems.items_desc.ilike(f"%{query.item_desc}%"))

    # ── Case Type ──
    if query.case_type:
        if (query.case_type or "").strip().upper() == "EXPORT CASE":
            q = q.filter(func.upper(CopsMaster.case_type) == "EXPORT CASE")
        else:
            # Arrival cases: case_type is NULL or not "EXPORT CASE"
            q = q.filter(
                or_(CopsMaster.case_type.is_(None), func.upper(CopsMaster.case_type) != "EXPORT CASE")
            )

    # To avoid duplicates if searching by item description
    if query.item_desc:
        q = q.distinct()

    # Dynamic sort — allowlisted columns only
    # os_no is VARCHAR so cast to Integer for correct numeric ordering (not "1","10","2")
    _os_no_int = cast(CopsMaster.os_no, Integer)
    _SORTABLE = {
        "os_no":             _os_no_int,
        "os_year":           CopsMaster.os_year,
        "os_date":           CopsMaster.os_date,
        "pax_name":          CopsMaster.pax_name,
        "total_items_value": CopsMaster.total_items_value,
        "total_payable":     CopsMaster.total_payable,
        "adjudication_date": CopsMaster.adjudication_date,
        "flight_date":       CopsMaster.flight_date,
    }
    sort_col = _SORTABLE.get(query.sort_by, CopsMaster.os_year)
    sort_fn = desc if query.sort_dir.lower() == "desc" else asc
    # Tie-break: always newest first (desc year, desc no) regardless of primary sort direction
    if query.sort_by in ("os_no", "os_year"):
        q = q.order_by(sort_fn(CopsMaster.os_year), sort_fn(_os_no_int))
    else:
        q = q.order_by(sort_fn(sort_col), desc(CopsMaster.os_year), desc(_os_no_int))
    
    # Pagination calculations
    total_count = q.count()
    limit = max(1, min(query.limit, 500))  # Cap page size at 500
    page = max(1, query.page)
    total_pages = (total_count + limit - 1) // limit
    
    # Fetch current page
    offset = (page - 1) * limit
    results = q.offset(offset).limit(limit).all()

    # Bulk-load items for all results in ONE query (eliminates N+1)
    items_map: dict = defaultdict(list)
    if results:
        keys = list({(r.os_no, r.os_year) for r in results})
        pair_filter = or_(*[and_(CopsItems.os_no == no, CopsItems.os_year == yr) for no, yr in keys])
        all_items = db.query(CopsItems).filter(
            pair_filter,
            or_(CopsItems.entry_deleted.is_(None), CopsItems.entry_deleted != "Y")
        ).order_by(CopsItems.os_no, CopsItems.os_year, CopsItems.items_sno).all()
        for item in all_items:
            items_map[(item.os_no, item.os_year)].append(item)

    response_data = []
    for case in results:
        items = items_map.get((case.os_no, case.os_year), [])

        case_dict = {
            "os_no": case.os_no,
            "os_year": case.os_year,
            "os_date": case.os_date,
            "pax_name": case.pax_name,
            "father_name": case.father_name,
            "passport_no": case.passport_no,
            "flight_no": case.flight_no,
            "flight_date": case.flight_date,
            "total_items_value": case.total_items_value or 0.0,
            "total_duty_amount": case.total_duty_amount or 0.0,
            "total_payable": case.total_payable or 0.0,
            "adjudication_date": case.adjudication_date,
            "is_draft": case.is_draft,
            "booked_by": case.booked_by,
            "os_printed": case.os_printed or "N",
            "shift": case.shift,
            "detention_date": case.detention_date,
            "pax_address1": case.pax_address1,
            "pax_address2": case.pax_address2,
            "pax_address3": case.pax_address3,
            "passport_date": case.passport_date,
            "port_of_dep_dest": case.port_of_dep_dest,
            "country_of_departure": case.country_of_departure,
            "pax_nationality": case.pax_nationality,
            "nationality": case.nationality,
            "date_of_departure": case.date_of_departure,
            "stay_abroad_days": case.stay_abroad_days,
            "residence_at": case.residence_at,
            "previous_visits": case.previous_visits,
            "confiscated_value": case.confiscated_value or 0.0,
            "redeemed_value": case.redeemed_value or 0.0,
            "re_export_value": case.re_export_value or 0.0,
            "rf_amount": case.rf_amount or 0.0,
            "ref_amount": case.ref_amount or 0.0,
            "pp_amount": case.pp_amount or 0.0,
            "supdts_remarks": (" ".join(filter(bool, [case.supdts_remarks, case.supdt_remarks2]))).strip() or None,
            "adjn_offr_remarks": (" ".join(filter(bool, [case.adjn_offr_remarks, case.adjn_offr_remarks1]))).strip() or None,
            "adj_offr_name": case.adj_offr_name,
            "adj_offr_designation": case.adj_offr_designation,
            "post_adj_br_entries": case.post_adj_br_entries,
            "post_adj_dr_no": case.post_adj_dr_no,
            "post_adj_dr_date": case.post_adj_dr_date,
            "case_type": case.case_type,
            "items": [
                {
                    "items_sno": i.items_sno,
                    "items_desc": i.items_desc,
                    "items_qty": i.items_qty or 0.0,
                    "items_uqc": i.items_uqc,
                    "items_value": i.items_value or 0.0,
                    "items_fa": i.items_fa or 0.0,
                    "items_fa_type": i.items_fa_type or 'value',
                    "items_fa_qty": i.items_fa_qty,
                    "items_fa_uqc": i.items_fa_uqc,
                    "items_release_category": i.items_release_category,
                    "items_duty_type": i.items_duty_type,
                    "value_per_piece": i.value_per_piece or 0.0,
                    "cumulative_duty_rate": i.cumulative_duty_rate or 0.0,
                } for i in items
            ]
        }
        
        response_data.append(OSQueryResponse.model_validate(case_dict))
        
    return OSQueryPaginatedResponse(
        items=response_data,
        total_count=total_count,
        page=page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


# ── Monthly Report ────────────────────────────────────────────────────────────

class MonthlyReportRow(BaseModel):
    os_no: str
    os_date: Optional[date]
    batch_aiu: Optional[str]
    flt_no: Optional[str]
    pax_name: Optional[str]
    nationality: Optional[str]
    passport_no: Optional[str]
    address: Optional[str]
    item_description: Optional[str]
    tags: Optional[str]
    quantity: Optional[str]
    value_in_rs: float
    oinO_no: str = ""
    date_of_oinO: str = ""
    rf_ref: float
    penalty: float
    duty_rs: float
    other_charges: str = ""
    total: float
    br_no: Optional[str]
    br_date: Optional[str]
    remarks: Optional[str]
    file_spot: str = "Spot"
    adjudicated_by_ac_dc: Optional[str]
    adjudicated_by_jc_adc: str = ""
    export_import: str
    column1: Optional[str]


@router.get("/monthly-report", response_model=List[MonthlyReportRow])
def get_monthly_report(
    month: int = QParam(..., ge=1, le=12, description="Month (1-12)"),
    year: int = QParam(..., ge=2000, le=2100, description="Year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns all submitted (non-draft, non-deleted) OS cases for the given month/year
    with all columns needed for the monthly register report.
    """
    # Filter: submitted, not deleted, in the given month/year
    q = (
        db.query(CopsMaster)
        .filter(
            CopsMaster.entry_deleted != "Y",
            CopsMaster.is_draft == "N",
            extract("month", CopsMaster.os_date) == month,
            extract("year", CopsMaster.os_date) == year,
        )
        .order_by(
            asc(cast(CopsMaster.os_no, Integer)),
        )
    )
    cases = q.all()

    if not cases:
        return []

    # Bulk-load items (N+1 prevention)
    keys = [(c.os_no, c.os_year) for c in cases]
    pair_filter = or_(*[
        and_(CopsItems.os_no == no, CopsItems.os_year == yr) for no, yr in keys
    ])
    all_items = (
        db.query(CopsItems)
        .filter(
            pair_filter,
            or_(CopsItems.entry_deleted.is_(None), CopsItems.entry_deleted != "Y"),
        )
        .order_by(CopsItems.os_no, CopsItems.os_year, CopsItems.items_sno)
        .all()
    )
    items_map: dict = defaultdict(list)
    for item in all_items:
        items_map[(item.os_no, item.os_year)].append(item)

    rows: list[MonthlyReportRow] = []
    for case in cases:
        items = items_map.get((case.os_no, case.os_year), [])

        # ── Col 8: Address ─────────────────────────────────────────────────
        addr_parts = [
            (case.pax_address1 or "").strip(),
            (case.pax_address2 or "").strip(),
            (case.pax_address3 or "").strip(),
        ]
        address = " ".join(p for p in addr_parts if p) or None

        # ── Col 9 & 11: Item Description / Quantity ────────────────────────
        item_desc = _build_item_desc(items)

        # ── Col 10: Tags ───────────────────────────────────────────────────
        tags = _classify_items_tags(items)

        # ── Col 12: Value in Rs (after free allowance) ─────────────────────
        # total_fa_value is 0 for old imported data, so subtraction is safe
        value_in_rs = max(0.0,
            (case.total_items_value or 0.0) - (case.total_fa_value or 0.0)
        )

        # ── Col 15: RF / R.E.F ─────────────────────────────────────────────
        rf_ref = (case.rf_amount or 0.0) + (case.ref_amount or 0.0)

        # ── Col 16: Penalty ────────────────────────────────────────────────
        penalty = case.pp_amount or 0.0

        # ── Col 17: Duty ───────────────────────────────────────────────────
        duty_rs = case.total_duty_amount or 0.0

        # ── Col 19: Total ─────────────────────────────────────────────────
        total = rf_ref + penalty + duty_rs

        # ── Col 20 & 21: BR No / BR Date ──────────────────────────────────
        br_no, br_date = _parse_br_entries(case.post_adj_br_entries)

        # ── Col 22: Remarks (DR.No. + date) ───────────────────────────────
        remarks = _format_dr_remarks(case.post_adj_dr_no, case.post_adj_dr_date) or None

        # ── Col 26: Export / Import ────────────────────────────────────────
        export_import = "Export" if (case.case_type or "").strip().upper() == "EXPORT CASE" else "Import"

        # ── Col 27: Confiscation label ────────────────────────────────────
        column1 = _confiscation_label(items) or None

        rows.append(MonthlyReportRow(
            os_no=case.os_no,
            os_date=case.os_date,
            batch_aiu=(case.booked_by or "").strip() or None,
            flt_no=case.flight_no,
            pax_name=case.pax_name,
            nationality=case.pax_nationality,
            passport_no=case.passport_no,
            address=address,
            item_description=item_desc or None,
            tags=tags or None,
            quantity=item_desc or None,
            value_in_rs=value_in_rs,
            rf_ref=rf_ref,
            penalty=penalty,
            duty_rs=duty_rs,
            total=total,
            br_no=br_no or None,
            br_date=br_date or None,
            remarks=remarks,
            file_spot=case.file_spot or "Spot",
            adjudicated_by_ac_dc=case.adj_offr_name or case.adj_offr_designation or None,
            export_import=export_import,
            column1=column1,
        ))

    return rows


# ── BR / DR Cross-Reference Lookup ───────────────────────────────────────────

def _os_status(case: CopsMaster) -> str:
    if case.adjudication_date or case.adj_offr_name:
        return "Adjudicated"
    if case.quashed == "Y":
        return "Quashed"
    if case.rejected == "Y":
        return "Rejected"
    return "Pending"


@router.get("/br/search")
def search_brs(
    q: Optional[str] = QParam(None, description="BR No, Pax Name, or Passport No"),
    year: Optional[int] = QParam(None),
    br_type: Optional[str] = QParam(None),
    page: int = QParam(1, ge=1),
    limit: int = QParam(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filt = [BrMaster.entry_deleted != "Y"]
    if q:
        if q.strip().lstrip("-").isdigit():
            filt.append(BrMaster.br_no == int(q.strip()))
        else:
            filt.append(or_(
                BrMaster.pax_name.ilike(f"%{q}%"),
                BrMaster.passport_no.ilike(f"%{q}%"),
            ))
    if year:
        filt.append(BrMaster.br_year == year)
    if br_type:
        filt.append(BrMaster.br_type == br_type)

    total = db.query(func.count(BrMaster.id)).filter(*filt).scalar() or 0
    rows = (
        db.query(BrMaster)
        .filter(*filt)
        .order_by(desc(BrMaster.br_date), desc(BrMaster.br_no))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "results": [
            {
                "br_no": r.br_no,
                "br_year": r.br_year,
                "br_date": r.br_date.isoformat() if r.br_date else None,
                "br_type": r.br_type,
                "pax_name": r.pax_name,
                "passport_no": r.passport_no,
                "total_duty_paid": r.br_amount or 0.0,
                "dr_no": r.dr_no,
                "os_no": r.os_no,
            }
            for r in rows
        ],
    }


@router.get("/br/{br_no}/{br_year}")
def get_br_detail(
    br_no: int,
    br_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    br = (
        db.query(BrMaster)
        .filter(BrMaster.br_no == br_no, BrMaster.br_year == br_year, BrMaster.entry_deleted != "Y")
        .first()
    )
    if not br:
        raise HTTPException(status_code=404, detail="B.R. not found")

    items = (
        db.query(BrItems)
        .filter(BrItems.br_no == br_no, BrItems.entry_deleted != "Y")
        .order_by(BrItems.items_sno)
        .all()
    )

    # Linked DR — br_master.dr_no stores the source DR number as a string
    linked_dr = None
    if br.dr_no:
        try:
            dr_no_int = int(str(br.dr_no).strip())
            dr = db.query(DrMaster).filter(
                DrMaster.dr_no == dr_no_int, DrMaster.entry_deleted != "Y"
            ).first()
            if dr:
                linked_dr = {
                    "dr_no": dr.dr_no, "dr_year": dr.dr_year,
                    "dr_date": dr.dr_date.isoformat() if dr.dr_date else None,
                    "dr_type": dr.dr_type, "pax_name": dr.pax_name,
                    "total_items_value": dr.total_items_value or 0.0,
                    "closure_ind": dr.closure_ind,
                }
        except (ValueError, TypeError):
            pass

    # Linked OS
    linked_os = None
    if br.os_no:
        os_case = db.query(CopsMaster).filter(
            CopsMaster.os_no == str(br.os_no), CopsMaster.entry_deleted != "Y"
        ).first()
        if os_case:
            linked_os = {
                "os_no": os_case.os_no, "os_year": os_case.os_year,
                "os_date": os_case.os_date.isoformat() if os_case.os_date else None,
                "pax_name": os_case.pax_name, "status": _os_status(os_case),
                "total_items_value": os_case.total_items_value or 0.0,
            }

    return {
        "br_no": br.br_no, "br_year": br.br_year,
        "br_date": br.br_date.isoformat() if br.br_date else None,
        "br_type": br.br_type, "br_shift": br.br_shift,
        "flight_no": br.flight_no,
        "flight_date": br.flight_date.isoformat() if br.flight_date else None,
        "pax_name": br.pax_name, "pax_nationality": br.pax_nationality,
        "passport_no": br.passport_no,
        "passport_date": br.passport_date.isoformat() if br.passport_date else None,
        "pax_address1": br.pax_address1, "pax_address2": br.pax_address2,
        "pax_address3": br.pax_address3,
        "total_items_value": br.total_items_value or 0.0,
        "total_duty_amount": br.total_duty_amount or 0.0,
        "rf_amount": br.rf_amount or 0.0, "pp_amount": br.pp_amount or 0.0,
        "br_amount": br.br_amount or 0.0, "challan_no": br.challan_no,
        "dr_no": br.dr_no, "dr_date": br.dr_date.isoformat() if br.dr_date else None,
        "os_no": br.os_no, "os_date": br.os_date.isoformat() if br.os_date else None,
        "batch_date": br.batch_date.isoformat() if br.batch_date else None,
        "batch_shift": br.batch_shift, "login_id": br.login_id,
        "items": [
            {
                "items_sno": it.items_sno, "items_desc": it.items_desc,
                "items_qty": it.items_qty or 0.0, "items_uqc": it.items_uqc,
                "items_value": it.items_value or 0.0, "items_fa": it.items_fa or 0.0,
                "items_duty": it.items_duty or 0.0, "items_duty_type": it.items_duty_type,
                "items_category": it.items_category,
            }
            for it in items
        ],
        "linked_dr": linked_dr,
        "linked_os": linked_os,
    }


@router.get("/dr/search")
def search_drs(
    q: Optional[str] = QParam(None, description="DR No, Pax Name, or Passport No"),
    year: Optional[int] = QParam(None),
    dr_type: Optional[str] = QParam(None),
    page: int = QParam(1, ge=1),
    limit: int = QParam(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filt = [DrMaster.entry_deleted != "Y"]
    if q:
        if q.strip().lstrip("-").isdigit():
            filt.append(DrMaster.dr_no == int(q.strip()))
        else:
            filt.append(or_(
                DrMaster.pax_name.ilike(f"%{q}%"),
                DrMaster.passport_no.ilike(f"%{q}%"),
            ))
    if year:
        filt.append(DrMaster.dr_year == year)
    if dr_type:
        filt.append(DrMaster.dr_type == dr_type)

    total = db.query(func.count(DrMaster.id)).filter(*filt).scalar() or 0
    rows = (
        db.query(DrMaster)
        .filter(*filt)
        .order_by(desc(DrMaster.dr_date), desc(DrMaster.dr_no))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "results": [
            {
                "dr_no": r.dr_no, "dr_year": r.dr_year,
                "dr_date": r.dr_date.isoformat() if r.dr_date else None,
                "dr_type": r.dr_type, "pax_name": r.pax_name,
                "passport_no": r.passport_no,
                "total_items_value": r.total_items_value or 0.0,
                "closure_ind": r.closure_ind, "os_no": r.os_no,
            }
            for r in rows
        ],
    }


@router.get("/dr/{dr_no}/{dr_year}")
def get_dr_detail(
    dr_no: int,
    dr_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Allow dr_year=0 as "any year" fallback
    q = db.query(DrMaster).filter(DrMaster.dr_no == dr_no, DrMaster.entry_deleted != "Y")
    if dr_year:
        q = q.filter(DrMaster.dr_year == dr_year)
    dr = q.order_by(desc(DrMaster.dr_date)).first()
    if not dr:
        raise HTTPException(status_code=404, detail="D.R. not found")

    items = (
        db.query(DrItems)
        .filter(DrItems.dr_no == dr_no)
        .order_by(DrItems.items_sno)
        .all()
    )

    # BRs that were issued against this DR (br_master.dr_no = str(dr_no))
    dr_no_str = str(dr_no)
    linked_brs = []
    brs = (
        db.query(BrMaster)
        .filter(BrMaster.dr_no == dr_no_str, BrMaster.entry_deleted != "Y")
        .order_by(desc(BrMaster.br_date))
        .all()
    )
    for b in brs:
        linked_brs.append({
            "br_no": b.br_no, "br_year": b.br_year,
            "br_date": b.br_date.isoformat() if b.br_date else None,
            "br_type": b.br_type, "total_duty_paid": b.br_amount or 0.0,
        })

    # Linked OS
    linked_os = None
    if dr.os_no:
        os_case = db.query(CopsMaster).filter(
            CopsMaster.os_no == str(dr.os_no), CopsMaster.entry_deleted != "Y"
        ).first()
        if os_case:
            linked_os = {
                "os_no": os_case.os_no, "os_year": os_case.os_year,
                "os_date": os_case.os_date.isoformat() if os_case.os_date else None,
                "pax_name": os_case.pax_name, "status": _os_status(os_case),
                "total_items_value": os_case.total_items_value or 0.0,
            }

    return {
        "dr_no": dr.dr_no, "dr_year": dr.dr_year,
        "dr_date": dr.dr_date.isoformat() if dr.dr_date else None,
        "dr_type": dr.dr_type, "flight_no": dr.flight_no,
        "flight_date": dr.flight_date.isoformat() if dr.flight_date else None,
        "pax_name": dr.pax_name, "passport_no": dr.passport_no,
        "passport_date": dr.passport_date.isoformat() if dr.passport_date else None,
        "pax_address1": dr.pax_address1, "pax_address2": dr.pax_address2,
        "pax_address3": dr.pax_address3,
        "total_items_value": dr.total_items_value or 0.0,
        "closure_ind": dr.closure_ind, "closure_remarks": dr.closure_remarks,
        "closure_date": dr.closure_date.isoformat() if dr.closure_date else None,
        "os_no": dr.os_no, "unique_no": dr.unique_no, "login_id": dr.login_id,
        "items": [
            {
                "items_sno": it.items_sno, "items_desc": it.items_desc,
                "items_qty": it.items_qty or 0.0, "items_uqc": it.items_uqc,
                "items_value": it.items_value or 0.0,
            }
            for it in items
        ],
        "linked_brs": linked_brs,
        "linked_os": linked_os,
    }

