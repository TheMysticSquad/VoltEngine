"""
  Unified API
----------------------

Single entry point for frontend / external systems.

Usage:
    from  .api import  API
"""

# ===============================
# Billing
# ===============================

from billing.prepaid_daily import PrepaidDailyBilling
from billing.prepaid_monthly import PrepaidMonthlyInvoice

# ===============================
# Operations
# ===============================

from  .operations.recharge import RechargeOperation
from  .operations.installment import InstallmentEngine
from  .operations.dps import DPSCalculator
from  .operations.excess_demand import ExcessDemandPenalty
from  .operations.load_change import LoadChange
from  operations.wallet import WalletService

# slab tariff helper (important — your new path)
from  operations.slab_tariff import SlabTariffCalculator

# ===============================

# Accounting
# ===============================

from  .accounting.ledger_engine import LedgerEngine

# ===============================
# Models
# ===============================

from  .models.consumer import Consumer
from  .models.meter import Meter
from  .models.tariff import Tariff
from  .models.period import Period


# =====================================================
# 🚀 MAIN FACADE CLASS (Frontend will use this)
# =====================================================

class  API:
    """
    Unified facade for  .
    Frontend should ONLY talk to this class.
    """

    # -----------------------------
    # DAILY BILL
    # -----------------------------
    @staticmethod
    def run_daily_billing(context: dict):
        engine = PrepaidDailyBilling()
        return engine.calculate(context)

    # -----------------------------
    # MONTHLY BILL
    # -----------------------------
    @staticmethod
    def run_monthly_invoice(context: dict):
        engine = PrepaidMonthlyInvoice()
        return engine.generate(context)

    # -----------------------------
    # RECHARGE
    # -----------------------------
    @staticmethod
    def recharge(context: dict):
        return RechargeOperation().execute(context)

    # -----------------------------
    # DPS
    # -----------------------------
    @staticmethod
    def calculate_dps(context: dict):
        return DPSCalculator().calculate(context)

    # -----------------------------
    # INSTALLMENT
    # -----------------------------
    @staticmethod
    def recover_installment(context: dict):
        return InstallmentEngine().recover(context)

    # -----------------------------
    # EXCESS DEMAND
    # -----------------------------
    @staticmethod
    def excess_demand(context: dict):
        return ExcessDemandPenalty().calculate(context)

    # -----------------------------
    # LEDGER
    # -----------------------------
    @staticmethod
    def build_ledger(context: dict):
        return LedgerEngine().post_entries(context)


# =====================================================
# ✅ EXPORTS
# =====================================================

__all__ = [
    " API",
    "Consumer",
    "Meter",
    "Tariff",
    "Period",
]
