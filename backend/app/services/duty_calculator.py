from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.masters import ItemCatMaster

class DutyCalculator:
    """
    Engine to calculate legacy B.R. Duties.
    Duty = (Value - FA) * Effective Rate
    Effective Rate relies on Item Categories.
    """
    def __init__(self, db: Session):
        self.db = db
        self.categories: Dict[str, ItemCatMaster] = {
            c.category_code: c for c in db.query(ItemCatMaster).all()
        }

    def calculate_item_duty(self, item_value: float, item_fa: float, category_code: str) -> dict:
        """
        Calculates all duty components for a single item based on its category.
        """
        dutiable_value = max(0, item_value - item_fa)
        
        if dutiable_value == 0 or not category_code:
            return {"bcd": 0, "cvd": 0, "cess": 0, "hec": 0, "duty": 0}

        category = self.categories.get(category_code)
        if not category:
            # Fallback to standard 35% if category unknown
            return {"bcd": 0, "cvd": 0, "cess": 0, "hec": 0, "duty": round(dutiable_value * 0.35)}

        # Legacy duty logic approximations: Custom rules applied here
        # E.g. BCD = dutiable * bcd_adv_rate
        # For full accuracy, we apply ad-valorem rates from DB.
        bcd  = round(dutiable_value * category.bcd_adv_rate, 2)
        cvd  = round((dutiable_value + bcd) * category.cvd_adv_rate, 2)
        cess = round(bcd * 0.10, 2)
        hec  = round(bcd * 0.03, 2)
        total_duty = round(bcd + cvd + cess + hec, 2)

        return {
            "bcd": bcd,
            "cvd": cvd,
            "cess": cess,
            "hec": hec,
            "duty": total_duty,
        }

    def process_br_items(self, items: List[dict]) -> tuple[float, float, float, List[dict]]:
        """
        Processes a list of items, calculates individual duties, and returns totals.
        Returns: (total_value, total_fa, total_duty, compiled_items)
        """
        total_val = 0.0
        total_fa = 0.0
        total_duty = 0.0
        compiled_items = []

        for item in items:
            val = item.get("items_value", 0.0)
            fa = item.get("items_fa", 0.0)
            cat = item.get("items_duty_type")
            
            duties = self.calculate_item_duty(val, fa, cat)
            duty = duties["duty"]
            
            total_val += val
            total_fa += fa
            total_duty += duty
            
            compiled_item = item.copy()
            compiled_item["items_bcd"] = duties["bcd"]
            compiled_item["items_cvd"] = duties["cvd"]
            compiled_item["items_cess"] = duties["cess"]
            compiled_item["items_hec"] = duties["hec"]
            compiled_item["items_duty"] = duty
            compiled_items.append(compiled_item)

        return total_val, total_fa, total_duty, compiled_items
