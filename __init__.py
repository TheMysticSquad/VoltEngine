"""
VoltEngine
==========

Utility-grade electricity billing engine supporting:
- LT Billing
- HT Billing
- Smart / Prepaid Billing

Designed as a pure Python library (no DB, no framework lock-in).
"""

__version__ = "0.1.0"

# ===============================
# Public Billing APIs
# ===============================

from voltengine.billing.prepaid_daily import PrepaidDailyBilling
from voltengine.billing.prepaid_monthly import PrepaidMonthlyInvoice

# (Add later when ready)
# from voltengine.billing.lt_billing import LTBilling
# from voltengine.billing.ht_billing import HTBilling


# ===============================
# Public Operations
# ===============================

from voltengine.operations.recharge import RechargeOperation
from voltengine.operations.installment import InstallmentEngine
from voltengine.operations.dps import DPSCalculator
from voltengine.operations.excess_demand import ExcessDemandPenalty


# ===============================
# Accounting
# ===============================

from voltengine.accounting.ledger_engine import LedgerEngine


# ===============================
# Models (optional public exposure)
# ===============================

from voltengine.models.consumer import Consumer
from voltengine.models.meter import Meter
from voltengine.models.tariff import Tariff
from voltengine.models.period import BillingPeriod

__all__ = [
    # Core
    "__version__",

    # Billing
    "PrepaidDailyBilling",
    "PrepaidMonthlyInvoice",

    # Operations
    "RechargeOperation",
    "InstallmentEngine",
    "DPSCalculator",
    "ExcessDemandPenalty",

    # Accounting
    "LedgerEngine",

    # Models
    "Consumer",
    "Meter",
    "Tariff",
    "BillingPeriod",
]
