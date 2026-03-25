from datetime import date
from typing import Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.baggage import BrMaster
from app.models.offence import CopsMaster
from app.models.detention import DrMaster

class BusinessRulesEngine:
    """
    Centralized validation engine enforcing the 31 rules from legacy COPS.
    """
    def __init__(self, db: Session):
        self.db = db

    # ── Rule 1: Passport Normalization & Overrides ──
    def normalize_passport(self, passport_no: str) -> str:
        if not passport_no:
            return ""
        p = passport_no.strip().upper()
        if p in ["DOMESTIC", "UNCLAIMED"]:
            return p
        return p

    # ── Rule 2: Free Allowance (FA) Availability Check ──
    def validate_fa_availability(self, passport_no: str, flight_date: date, current_fa_claim: float) -> Tuple[bool, float]:
        """
        Validates if passenger has exhausted their FA limit (default 50k) 
        based on passport and flight date within the same day/trip.
        """
        if passport_no in ["DOMESTIC", "UNCLAIMED", ""]:
            return True, current_fa_claim

        # Find existing BRs for this passport on this flight_date
        existing_brs = self.db.query(BrMaster).filter(
            BrMaster.passport_no == passport_no,
            BrMaster.flight_date == flight_date,
            BrMaster.entry_deleted == "N"
        ).all()

        fa_used = sum(br.total_fa_availed for br in existing_brs if br.total_fa_availed is not None)
        
        if fa_used + current_fa_claim > settings.FA_LIMIT:
            diff = settings.FA_LIMIT - fa_used
            if diff <= 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Passenger already availed full F.A. Limit of {settings.FA_LIMIT} today."
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Passenger can only avail Rs.{diff} F.A. Limit now."
                )
        return True, current_fa_claim

    # ── Rule 3: Flight Date Timeline Constraint ──
    def validate_flight_date(self, flight_date: date, batch_date: date):
        if flight_date > batch_date:
            raise HTTPException(status_code=400, detail="Check Flight Date! Cannot be in the future.")
        # Legacy warning, not strict rejection
        # if (batch_date - flight_date).days > 2:
        #     return "Warning: Flight date is more than 2 days old."

    # ── Rule 4: Passenger DOB & Departure Timeline ──
    def validate_pax_dates(self, dob: Optional[date], departure: Optional[date], batch_date: date):
        if dob and dob > batch_date:
            raise HTTPException(status_code=400, detail="Date of Birth Should Not be Greater Than Current Batch Date...")
        if departure and departure > batch_date:
            raise HTTPException(status_code=400, detail="Date of Departure Should Not be Greater Than Current Batch Date...")

    # ── Rule 5: O.S. Online Adjudication Boundaries ──
    def validate_os_adjudication_boundaries(self, total_value: float):
        if total_value > settings.ADJUDICATION_VALUE_LIMIT:
            raise HTTPException(
                status_code=400, 
                detail=f"Total Value exceeds \u20b9{settings.ADJUDICATION_VALUE_LIMIT:,.2f}. Online adjudication cannot be done! Generate System O.S. Form."
            )

    # ── Rule 6: Duplicate Passport Check (Warning standard) ──
    def check_duplicate_passport(self, passport_no: str) -> bool:
        if passport_no in ["DOMESTIC", "UNCLAIMED", ""]:
            return False
            
        count = self.db.query(BrMaster).filter(
            BrMaster.passport_no == passport_no,
            BrMaster.entry_deleted == "N"
        ).count()
        
        count += self.db.query(CopsMaster).filter(
            CopsMaster.passport_no == passport_no,
            CopsMaster.entry_deleted == "N"
        ).count()
        
        return count > 0

    # ── Rule 7: Remarks Length Limitation ──
    def validate_remarks_length(self, remarks: str):
        if remarks and len(remarks) > settings.ADJN_REMARKS_MAX_CHARS:
            raise HTTPException(
                status_code=400,
                detail=f"The Remarks of the Adjudicating Officer exceeds {settings.ADJN_REMARKS_MAX_CHARS} Characters. Please Use the Option of 'Print Adjn. Order On Legal Size Blank Paper'..."
            )
