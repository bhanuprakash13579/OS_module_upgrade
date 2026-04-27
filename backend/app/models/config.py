"""
System Configuration Models.
Tables: shift_timing_master, margin_master, data_master, batch_master, batch_with_many_dc,
        print_template_config, baggage_rules_config, special_item_allowances
"""
from sqlalchemy import Column, String, Float, Date, Integer, Boolean, Text, DateTime
from app.database import Base


class ShiftTimingMaster(Base):
    """
    Legacy table: shift_timing_master
    Default seed: (7, 19, 19, 7) — matches old module
    Night shift auto-derives by inverting day shift hours.
    """
    __tablename__ = "shift_timing_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_shift_from_hrs = Column(Integer, default=7)
    day_shift_to_hrs = Column(Integer, default=19)
    night_shift_from_hrs = Column(Integer, default=19)
    night_shift_to_hrs = Column(Integer, default=7)


class MarginMaster(Base):
    """
    Legacy table: margin_master
    Controls print margins for B.R. and D.R. printouts.
    Default seed: (0.310, 0.310)
    """
    __tablename__ = "margin_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    br_top_margin = Column(Float, default=0.310)
    dr_top_margin = Column(Float, default=0.310)


class DataMaster(Base):
    """
    Legacy table: data_master
    Stores the current batch date.
    """
    __tablename__ = "data_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_date = Column(Date)


class BatchMaster(Base):
    """
    Legacy table: batch_master
    Current active batch date and shift.
    """
    __tablename__ = "batch_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_batch_date = Column(Date)
    current_batch_shift = Column(String(20))  # Day / Night


class FeatureFlags(Base):
    """
    Feature flag table — single row (id=1).
    Controls which optional modules are enabled for this deployment.
    Default: all flags OFF (admin must explicitly enable each feature).
    """
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    apis_enabled = Column(Boolean, default=False, nullable=False)
    session_timeout_minutes = Column(Integer, default=480, nullable=False)
    # Trial counter — trial_start_date set on first startup; trial_disabled=1 → permanent install
    # trial_days = configurable trial duration (defaults to 30 if not set)
    trial_start_date = Column(String, nullable=True)
    trial_disabled = Column(Integer, default=0, nullable=False)
    trial_days = Column(Integer, default=30, nullable=False)


class PrintTemplateConfig(Base):
    """
    Versioned static text for the OS print form.
    Point-in-time lookup: WHERE field_key=X AND effective_from <= os_date
                          ORDER BY effective_from DESC LIMIT 1
    """
    __tablename__ = "print_template_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    field_key   = Column(String(100), nullable=False, index=True)
    field_label = Column(String(200))           # human-readable label for admin UI
    field_value = Column(Text, nullable=False)  # the text to display/print
    effective_from = Column(Date, nullable=False, index=True)
    created_by  = Column(String(100))
    created_at  = Column(DateTime)


class BaggageRulesConfig(Base):
    """
    Versioned numeric baggage rules (FA limits, gold limits, etc.).
    rule_uqc: INR | GMS | DAYS | LTR | NOS
    rule_value = 0 means 'no cap' (for gold_value_cap_*)
    """
    __tablename__ = "baggage_rules_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_key    = Column(String(100), nullable=False, index=True)
    rule_label  = Column(String(200))
    rule_value  = Column(Float, nullable=False)
    rule_uqc    = Column(String(20))
    effective_from = Column(Date, nullable=False, index=True)
    created_by  = Column(String(100))
    created_at  = Column(DateTime)


class SpecialItemAllowance(Base):
    """
    Per-item free provisions separate from general FA.
    keywords: comma-separated match words (lowercase).
    Admin can add any new item at any time with its own effective_from date.
    active = 'N' soft-deletes the allowance.
    """
    __tablename__ = "special_item_allowances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name      = Column(String(100), nullable=False)
    keywords       = Column(Text)       # comma-separated, lowercase
    allowance_qty  = Column(Float, nullable=False)
    allowance_uqc  = Column(String(20))
    effective_from = Column(Date, nullable=False, index=True)
    active         = Column(String(1), default='Y')
    created_by     = Column(String(100))
    created_at     = Column(DateTime)


class BatchWithManyDc(Base):
    """
    Legacy table: batch_with_many_dc
    Handles batches with multiple DC/AC officers.
    INSERT INTO batch_with_many_dc(current_batch_date, current_batch_shift,
                                    marked_dc_codes, correct_dc_name)
    """
    __tablename__ = "batch_with_many_dc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_batch_date = Column(Date)
    current_batch_shift = Column(String(20))
    marked_dc_codes = Column(String(500))
    correct_dc_name = Column(String(200))
    sdo_code = Column(String(50))
