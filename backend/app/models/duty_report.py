"""
Duty Collection Report models.
Tables: dr_tariffs, dr_item_types, dr_sessions, dr_entries,
        dr_dr_entries (DR sub-table), dr_os_entries (OS sub-table),
        dr_settings (module-level greeting config),
        dr_formula_rules (user-configurable per-column formulas)
"""
from sqlalchemy import (
    Column, String, Float, Date, Integer, Boolean,
    DateTime, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.sql import func
from app.database import Base


class DrTariff(Base):
    """
    Rate history table. Insert a new row (with effective_from) whenever rates change.
    Old sessions hold a tariff_id snapshot — their computed duties are never recomputed.
    """
    __tablename__ = "dr_tariffs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    effective_from = Column(Date, nullable=False)
    label = Column(String(200), nullable=True)  # optional human note e.g. "Post Budget 2025"
    # Baggage (general items)
    baggage_rate = Column(Float, default=0.35, nullable=False)
    # Liquor
    liquor_duty_rate = Column(Float, default=0.50, nullable=False)
    aidc_liquor_rate = Column(Float, default=1.0, nullable=False)
    # Gold (BCD)
    gold_bcd_rate = Column(Float, default=0.35, nullable=False)
    aidc_gold_rate = Column(Float, default=0.05, nullable=False)
    # Gold (Consolidated rate)
    gold_cons_bcd_rate = Column(Float, default=0.10, nullable=False)
    aidc_gold_cons_rate = Column(Float, default=0.05, nullable=False)
    # Silver (BCD)
    silver_bcd_rate = Column(Float, default=0.35, nullable=False)
    aidc_silver_rate = Column(Float, default=0.05, nullable=False)
    # Silver (Consolidated rate)
    silver_cons_rate = Column(Float, default=0.05, nullable=False)
    aidc_silver_cons_rate = Column(Float, default=0.05, nullable=False)

    created_at = Column(DateTime, server_default=func.now())


class DrItemType(Base):
    """User-created and system item type names for the description combobox."""
    __tablename__ = "dr_item_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    usage_count = Column(Integer, default=0, nullable=False)
    # is_system=True means pinned (GOLD, SILVER, LIQUOR, etc.) — cannot be deleted
    is_system = Column(Boolean, default=False, nullable=False)


class DrSession(Base):
    """One row per shift per date. Unique on (report_date, shift)."""
    __tablename__ = "dr_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False)
    shift = Column(String(10), nullable=False)       # 'DAY' or 'NIGHT'
    batch_name = Column(String(100), nullable=True)  # e.g. 'C Batch'
    tariff_id = Column(Integer, ForeignKey("dr_tariffs.id"), nullable=True)
    challan_no = Column(String(50), nullable=True)    # SBI challan / bank receipt no.
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    submitted_at = Column(DateTime, nullable=True)   # set when user clicks Submit
    submitted_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("report_date", "shift", name="uq_dr_session_date_shift"),
    )


class DrEntry(Base):
    """
    One row per item entry (maps to one Excel row in DAY/NIGHT sheet).
    sl_no is null for sub-rows (same BR, multiple items).
    All computed duties are stored so historical records are never affected
    when tariff rates change in the future.
    """
    __tablename__ = "dr_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("dr_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False)
    sl_no = Column(Integer, nullable=True)       # null = sub-row for same BR
    br_no = Column(String(50), nullable=True)
    os_ref = Column(String(100), nullable=True)  # "OS No." column (col C)
    item_desc = Column(String(200), nullable=True)
    dutiable_value = Column(Float, default=0)
    gold_weight_gms = Column(Float, default=0)
    # ── Auto-computed duties (stored, not recalculated from current rates) ──
    baggage_duty = Column(Float, default=0)
    liquor_duty = Column(Float, default=0)
    cigarette_duty = Column(Float, default=0)    # manual
    sw_sc = Column(Float, default=0)             # manual: SW SC on Bagg/Lqr/Cig
    gold_duty_bcd = Column(Float, default=0)
    gold_duty_cons = Column(Float, default=0)
    silver_duty_cons = Column(Float, default=0)
    sws_on_gold = Column(Float, default=0)       # manual
    aidc_gold_silver = Column(Float, default=0)
    sws_on_silver = Column(Float, default=0)     # manual
    aidc_on_liquor = Column(Float, default=0)
    redemption_fine = Column(Float, default=0)   # manual
    reexport_fine = Column(Float, default=0)     # manual
    personal_penalty = Column(Float, default=0)  # manual
    other_charges = Column(Float, default=0)     # manual
    fuel_duty = Column(Float, default=0)         # manual
    cess_on_cig = Column(Float, default=0)       # manual: CESS on Cigarettes (col 26 in monthly register)
    total_duty = Column(Float, default=0)        # ROUND(SUM(G:V), 0)
    flight_no = Column(String(20), nullable=True)
    is_sbi_challan = Column(Boolean, default=False)  # red row = SBI Challan offline payment
    is_offline_br = Column(Boolean, default=False)   # red BR No. text = offline (manual) BR
    # JSON list of field names that were manually overridden (vs auto-computed)
    overrides = Column(Text, nullable=True)


class DrDrEntry(Base):
    """DR (Detention Register) sub-table per session."""
    __tablename__ = "dr_dr_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("dr_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False)
    dr_no = Column(String(50), nullable=True)
    amount = Column(Float, default=0)
    item_desc = Column(String(500), nullable=True)
    remarks = Column(String(500), nullable=True)


class DrOsEntry(Base):
    """OS (Offence Sheet) sub-table per session."""
    __tablename__ = "dr_os_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("dr_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False)
    os_no = Column(String(50), nullable=True)
    amount = Column(Float, default=0)
    item_desc = Column(String(500), nullable=True)
    remarks = Column(String(500), nullable=True)


class DrSettings(Base):
    """Module-level settings — single row (id=1)."""
    __tablename__ = "dr_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    greeting_recipients = Column(String(500), default="Sir", nullable=False)
    # e.g. "AC Sir/BS Sir" — shown in the WhatsApp message header


class DrFormulaRule(Base):
    """
    User-configurable formula rules for duty column auto-computation.

    Each rule says: "for items matching [condition], compute [target_column] as [expression]."
    Rules are evaluated in sort_order; the FIRST matching rule for a column wins.
    Changing a rule only affects NEW entries — existing DrEntry rows store flat values and
    are never recomputed, so historical data is fully protected.

    Expression variables:
      value          = dutiable_value
      weight         = gold_weight_gms
      baggage_rate, liquor_duty_rate, aidc_liquor_rate,
      gold_bcd_rate, aidc_gold_rate, gold_cons_bcd_rate, aidc_gold_cons_rate,
      silver_bcd_rate, aidc_silver_rate, silver_cons_rate, aidc_silver_cons_rate
    """
    __tablename__ = "dr_formula_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sort_order = Column(Integer, default=0, nullable=False)
    target_column = Column(String(50), nullable=False)   # DrEntry field name
    column_label = Column(String(120))                   # display name shown in UI
    condition_type = Column(String(10), default="all", nullable=False)
    # "all"    → applies to every item
    # "only"   → applies only to items in condition_items
    # "except" → applies to all items NOT in condition_items
    condition_items = Column(Text, default="")           # comma-separated item names
    expression = Column(Text, default="")                # formula; empty = manual/0
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # ── Version history ──────────────────────────────────────────────────────
    #
    # A rule is never rewritten. Changing a formula writes a new row carrying the
    # same lineage_id and the date it takes effect from, and the old row stays
    # exactly as it was. A shift then computes on the rule that was in force on
    # its own report date: a sheet from last year reopened today recomputes the
    # way it did last year, and today's sheet uses today's formula.
    #
    # The figures already entered were never at risk — a duty is worked out as
    # the row is typed and stored as a flat amount, never recomputed. This is
    # about the row somebody edits after the formula has moved on.
    lineage_id = Column(Integer, index=True)             # the rule this descends from
    effective_from = Column(Date, index=True)            # in force from this date
    changed_by = Column(String(120))                     # who wrote this version
