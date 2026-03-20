"""
Central model registry — imports ALL models so SQLAlchemy can discover them.
68 tables total.
"""
# Auth & Config (7 tables)
from app.models.auth import User, IpAddrsTable
from app.models.config import (
    ShiftTimingMaster, MarginMaster, DataMaster,
    BatchMaster, BatchWithManyDc, FeatureFlags
)
from app.models.security import AllowedDevice

# Masters (9 tables)
from app.models.masters import (
    DcMaster, AirlinesMast, ArrivalFlightMaster,
    AirportMaster, NationalityMaster, PortMaster,
    ItemCatMaster, DutyRateMaster, BrNoLimits
)

# Core Transactions (9 tables)
from app.models.baggage import BrMaster, BrItems
from app.models.offence import CopsMaster, CopsItems, OsMaster, ItemTrans
from app.models.detention import DrMaster, DrItems
from app.models.fuel import FuelMaster

# Warehouse (6 tables)
from app.models.warehouse import (
    WhMaster, WhItems, WhRelease, WhLocationChange,
    ValuablesMaster, ValuablesItems
)

# MHB (4 tables)
from app.models.mhb import MahazarMaster, MahazarItems, MhbMaster, MhbItems

# Appeal (2 tables)
from app.models.appeal import AppealMaster, AppealItems

# Revenue (3 tables)
from app.models.revenue import Revenue, RevChallans, ChallanMaster

# Audit/Tracking (22 tables)
from app.models.audit import (
    CopsMasterDeleted, CopsItemsDeleted,
    CopsMasterTemp, CopsItemsTemp,
    OsMasterDeleted, ItemTransDeleted,
    OldBrMaster, OldBrItems,
    ModifiedMasterBrNos, ModifiedItemBrNos,
    DupBRsDeletedInTfr, TypeChangedBrs,
    DrUpdateFromBr,
    UosMaster, UosItems,
    ValuationMaster, ValuationItems,
    ShortCollectionMaster, DriMaster,
    FltManifests, BrPrintGaps,
    OsItemCompareRemarks, ValItemsReconsRemarks,
    ValMasterReconsRemarks, ValuablesItemsReconsRemarks,
    WhItemsReconsRemarks, WhMasterReconsRemarks,
)

# Report Staging (6 tables)
from app.models.reports import (
    OsRptMaster, OsRptItems,
    WhGnlRptMaster, WhGnlRptItems,
    WhValRptMaster, WhValRptItems,
)

__all__ = [
    # Auth
    "User", "IpAddrsTable",
    # Config
    "ShiftTimingMaster", "MarginMaster", "DataMaster",
    "BatchMaster", "BatchWithManyDc", "FeatureFlags",
    # Security
    "AllowedDevice",
    # Masters
    "DcMaster", "AirlinesMast", "ArrivalFlightMaster",
    "AirportMaster", "NationalityMaster", "PortMaster",
    "ItemCatMaster", "DutyRateMaster", "BrNoLimits",
    # Baggage
    "BrMaster", "BrItems",
    # Offence
    "CopsMaster", "CopsItems", "OsMaster", "ItemTrans",
    # Detention
    "DrMaster", "DrItems",
    # Fuel
    "FuelMaster",
    # Warehouse
    "WhMaster", "WhItems", "WhRelease", "WhLocationChange",
    "ValuablesMaster", "ValuablesItems",
    # MHB
    "MahazarMaster", "MahazarItems", "MhbMaster", "MhbItems",
    # Appeal
    "AppealMaster", "AppealItems",
    # Revenue
    "Revenue", "RevChallans", "ChallanMaster",
    # Audit
    "CopsMasterDeleted", "CopsItemsDeleted",
    "CopsMasterTemp", "CopsItemsTemp",
    "OsMasterDeleted", "ItemTransDeleted",
    "OldBrMaster", "OldBrItems",
    "ModifiedMasterBrNos", "ModifiedItemBrNos",
    "DupBRsDeletedInTfr", "TypeChangedBrs",
    "DrUpdateFromBr",
    "UosMaster", "UosItems",
    "ValuationMaster", "ValuationItems",
    "ShortCollectionMaster", "DriMaster",
    "FltManifests", "BrPrintGaps",
    "OsItemCompareRemarks", "ValItemsReconsRemarks",
    "ValMasterReconsRemarks", "ValuablesItemsReconsRemarks",
    "WhItemsReconsRemarks", "WhMasterReconsRemarks",
    # Reports
    "OsRptMaster", "OsRptItems",
    "WhGnlRptMaster", "WhGnlRptItems",
    "WhValRptMaster", "WhValRptItems",
]
