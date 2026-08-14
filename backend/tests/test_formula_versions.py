"""A formula change applies from the day it is made, and never backwards.

The figures already on a sheet were never at risk — a duty is worked out as the
row is typed and stored as a flat amount. This covers the row somebody edits
after the formula has moved on: the shift recomputes on the rule that was in
force on its own report date.

Run: python3 backend/tests/test_formula_versions.py
"""
import os, sys, tempfile
os.environ["COPS_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import date, timedelta
from app.database import Base, SessionLocal, engine
import app.models
from app.models.duty_report import DrFormulaRule
from app.api.duty_report import _rules_in_force

Base.metadata.create_all(bind=engine)
db = SessionLocal()

TODAY = date.today()
LAST_YEAR = TODAY - timedelta(days=400)

# The rule as it stood, and the revision made today.
old = DrFormulaRule(sort_order=1, target_column="baggage_duty", column_label="Baggage duty",
                    condition_type="all", condition_items="", expression="value * 0.35",
                    is_active=True, effective_from=date(1900, 1, 1))
db.add(old); db.flush(); old.lineage_id = old.id
new = DrFormulaRule(sort_order=1, target_column="baggage_duty", column_label="Baggage duty",
                    condition_type="all", condition_items="", expression="value * 0.38",
                    is_active=True, lineage_id=old.id, effective_from=TODAY,
                    changed_by="officer1")
# An unrelated rule, to prove only the one column moved.
other = DrFormulaRule(sort_order=2, target_column="liquor_duty", column_label="Liquor Duty",
                      condition_type="only", condition_items="LIQUOR",
                      expression="value * 0.5", is_active=True, effective_from=date(1900, 1, 1))
db.add_all([new, other]); db.flush(); other.lineage_id = other.id
db.commit()

def expr_on(day, column="baggage_duty"):
    return [r.expression for r in _rules_in_force(db, day) if r.target_column == column]

assert expr_on(LAST_YEAR) == ["value * 0.35"], f"last year's sheet keeps last year's formula: {expr_on(LAST_YEAR)}"
assert expr_on(TODAY) == ["value * 0.38"], f"today's sheet uses today's: {expr_on(TODAY)}"
assert expr_on(TODAY - timedelta(days=1)) == ["value * 0.35"], "the day before the change is unaffected"
print(f"  a shift on {LAST_YEAR}  -> {expr_on(LAST_YEAR)[0]}")
print(f"  a shift today          -> {expr_on(TODAY)[0]}")

# One rule per lineage on any given day — never both versions at once.
same_day = _rules_in_force(db, TODAY)
assert len([r for r in same_day if r.target_column == "baggage_duty"]) == 1, \
    "a column has one rule in force at a time"
assert expr_on(TODAY, "liquor_duty") == ["value * 0.5"], "the other column was not touched"
print(f"  the untouched column   -> {expr_on(TODAY, 'liquor_duty')[0]}")

# A rule written before any of this, with no lineage recorded, is its own.
orphan = DrFormulaRule(sort_order=3, target_column="fuel_duty", condition_type="all",
                       expression="value * 0.1", is_active=True)
db.add(orphan); db.commit()
assert "value * 0.1" in [r.expression for r in _rules_in_force(db, TODAY)], \
    "a rule with no version history still applies"
print("  a rule predating all this still applies")

# The old version is still in the table, whole.
kept = db.query(DrFormulaRule).filter(DrFormulaRule.lineage_id == old.id).all()
assert len(kept) == 2 and {r.expression for r in kept} == {"value * 0.35", "value * 0.38"}, \
    "both versions are kept; nothing is overwritten"
print("  both versions kept, author recorded:", [r.changed_by for r in kept])
print("  all checks passed")
