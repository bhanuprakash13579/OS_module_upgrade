import datetime as ext_datetime
from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, constr, field_validator
from app.config import settings


class CopsItemBase(BaseModel):
    items_sno: int
    items_desc: Optional[str] = None
    items_qty: float = 0.0
    items_uqc: Optional[str] = None
    value_per_piece: float = 0.0
    items_value: float = 0.0     # Total Value
    items_fa: float = 0.0
    items_fa_type: str = 'value'          # 'value' = Rs amount, 'qty' = quantity-based
    items_fa_qty: Optional[float] = None
    items_fa_uqc: Optional[str] = None
    cumulative_duty_rate: float = 0.0
    items_duty_type: Optional[str] = None
    items_category: Optional[str] = None
    items_release_category: Optional[str] = None
    items_sub_category: Optional[str] = None
    items_dr_no: int = 0
    items_dr_year: int = 0

class CopsItemCreate(CopsItemBase):
    pass

class CopsItemOut(CopsItemBase):
    id: int
    os_no: str
    os_date: date
    os_year: int
    items_duty: float
    model_config = ConfigDict(from_attributes=True)


class CopsMasterBase(BaseModel):
    # Core identifiers / meta
    os_no: Optional[str] = None
    os_date: Optional[date] = None

    booked_by: Optional[str] = None
    shift: Optional[str] = None
    detention_date: Optional[date] = None
    case_type: Optional[str] = None
    
    pax_name: Optional[str] = None
    pax_nationality: Optional[str] = None
    passport_no: Optional[str] = None
    passport_date: Optional[date] = None
    pp_issue_place: Optional[str] = None
    pax_address1: Optional[str] = None
    pax_address2: Optional[str] = None
    pax_address3: Optional[str] = None
    pax_date_of_birth: Optional[date] = None
    pax_status: Optional[str] = None
    residence_at: Optional[str] = None
    
    country_of_departure: Optional[str] = None
    port_of_dep_dest: Optional[str] = None
    date_of_departure: Optional[str] = None
    stay_abroad_days: Optional[int] = None
    flight_no: Optional[str] = None
    flight_date: Optional[date] = None
    
    dutiable_value: float = 0.0
    redeemed_value: float = 0.0
    re_export_value: float = 0.0
    confiscated_value: float = 0.0
    rf_amount: float = 0.0
    pp_amount: float = 0.0
    ref_amount: float = 0.0
    br_amount: float = 0.0

    detained_by: Optional[str] = None
    seal_no: Optional[str] = None
    nationality: Optional[str] = None
    dr_no: Optional[str] = None
    dr_year: Optional[int] = None
    total_drs: int = 0
    
    previous_os_details: Optional[str] = None
    previous_visits: Optional[str] = None
    father_name: Optional[str] = None
    old_passport_no: Optional[str] = None
    total_pkgs: int = 0
    supdts_remarks: Optional[str] = None

    @field_validator('supdts_remarks')
    @classmethod
    def check_supdt_remarks_length(cls, v):
        if v and len(v) > settings.SUPDT_REMARKS_MAX_CHARS:
            raise ValueError(
                f"Supdt's Remarks exceeds maximum limit of {settings.SUPDT_REMARKS_MAX_CHARS} characters."
            )
        return v

    is_draft: Optional[str] = "N"
    is_offline_adjudication: Optional[str] = None
    file_spot: Optional[str] = None


class CopsMasterCreate(CopsMasterBase):
    items: List[CopsItemCreate]


class CopsMasterOut(CopsMasterBase):
    id: int
    os_no: str
    os_date: date
    os_year: int
    location_code: Optional[str] = None
    total_items: int = 0
    total_items_value: float = 0.0
    total_duty_amount: float = 0.0
    total_payable: float = 0.0
    
    adjudication_date: Optional[date] = None
    adj_offr_name: Optional[str] = None
    adj_offr_designation: Optional[str] = None
    adjn_offr_remarks: Optional[str] = None
    adjudication_time: Optional[datetime] = None
    online_adjn: Optional[str] = None
    
    os_printed: str = 'N'
    is_offline_adjudication: Optional[str] = None
    file_spot: Optional[str] = None
    entry_deleted: str = 'N'
    closure_ind: Optional[str] = None

    # Post-adjudication metadata (BR/DR receipts — never touched by adjudication workflow)
    post_adj_br_entries: Optional[str] = None   # JSON string
    post_adj_dr_no:      Optional[str] = None
    post_adj_dr_date:    Optional[date] = None
    
    quashed: str = 'N'
    quashed_by: Optional[str] = None
    quash_reason: Optional[str] = None
    quash_date: Optional[date] = None
    rejected: str = 'N'
    reject_reason: Optional[str] = None
    
    items: List[CopsItemOut] = []
    model_config = ConfigDict(from_attributes=True)

class CopsMasterPagedOut(BaseModel):
    """Paginated response for OS case list."""
    total: int
    page: int
    per_page: int
    items: List[CopsMasterOut]

class OSActionReason(BaseModel):
    reason: str

class AdjudicationCreate(BaseModel):
    """Full adjudication payload — mirrors ONLINE ADJN app fields."""
    # Officer details
    adj_offr_name: str
    adj_offr_designation: str
    adjudication_date: Optional[date] = None   # defaults to today if not given

    # Disposal values per item category
    confiscated_value: float = 0.0
    redeemed_value: float = 0.0
    re_export_value: float = 0.0

    # Financial demands
    rf_amount: float = 0.0      # Redemption Fine
    pp_amount: float = 0.0      # Personal Penalty
    ref_amount: float = 0.0     # Re-Export Fine

    # Per-item release categories: { item_id_str: 'CONFS' | 'RF' | 'REF' }
    item_categories: Optional[Dict[str, str]] = None

    # Gist / Remarks (max 700 chars enforced)
    adjn_offr_remarks: str = ""

    # Whether to close the case (set closure_ind = 'Y')
    close_case: bool = False

    @field_validator('adjn_offr_remarks')
    @classmethod
    def check_remarks_length(cls, v):
        if len(v) > settings.ADJN_REMARKS_MAX_CHARS:
            raise ValueError(
                f"The Remarks of the Adjudicating Officer exceeds {settings.ADJN_REMARKS_MAX_CHARS} Characters. "
                f"Please Use the Option of 'Print Adjn. Order On Legal Size Blank Paper' From the Print Menu."
            )
        return v


class PostAdjBrEntry(BaseModel):
    """A single Bank Receipt entry linked to a post-adjudication payment."""
    no:   str
    date: Optional[ext_datetime.date] = None


class PostAdjUpdate(BaseModel):
    """
    Payload for PATCH /os/{os_no}/{os_year}/post-adj.
    Strictly limited to post-adjudication BR/DR metadata.
    No adjudication fields are touched.
    """
    br_entries: List[PostAdjBrEntry] = []
    dr_no:      Optional[str]  = None
    dr_date:    Optional[date] = None


class OfflineAdjudicationComplete(BaseModel):
    """Payload to complete offline adjudication (capture officer details)."""
    adj_offr_name: str          # MANDATORY
    adj_offr_designation: str   # MANDATORY
    adjudication_date: Optional[date] = None   # defaults to today if None
    # Optional financial details
    rf_amount: float = 0.0
    pp_amount: float = 0.0
    ref_amount: float = 0.0
    confiscated_value: float = 0.0
    redeemed_value: float = 0.0
    re_export_value: float = 0.0
    adjn_offr_remarks: Optional[str] = None
    close_case: bool = False

    @field_validator('adjn_offr_remarks')
    @classmethod
    def check_remarks_length(cls, v):
        if v and len(v) > settings.ADJN_REMARKS_MAX_CHARS:
            raise ValueError(
                f"Remarks exceeds {settings.ADJN_REMARKS_MAX_CHARS} characters."
            )
        return v
