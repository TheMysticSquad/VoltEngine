from strategies.base import BillingStrategy
from services.prepaid_charges import PrepaidChargeService
from services.dps import DPSService
from services.installment import InstallmentService
from services.wallet import WalletService
from engine.response import BillingResponse

class PrepaidBilling(BillingStrategy):

    def calculate(self, ctx):

        prepaid_service = PrepaidChargeService()
        dps_service = DPSService()
        inst_service = InstallmentService()
        wallet_service = WalletService()

        # 1. DPS on arrear
        dps = dps_service.calculate_daily_dps(
            ctx.consumer.arrear_balance,
            ctx.tariff.dps_monthly_rate
        )
        ctx.consumer.arrear_balance += dps

        # 2. Daily prepaid charges
        daily_amount, breakup = prepaid_service.calculate_daily(
            ctx.meter,
            ctx.tariff,
            ctx.period
        )

        # 3. Installment deduction
        installment = inst_service.get_daily_installment(
            ctx.consumer.installment
        )
        ctx.consumer.arrear_balance -= installment

        # 4. Wallet deduction
        total_deduction = daily_amount + installment
        closing_balance = wallet_service.deduct(
            ctx.consumer, total_deduction
        )

        breakup["installment"] = installment
        breakup["dps"] = dps

        return BillingResponse(
            billing_type="PREPAID",
            amount=total_deduction,
            breakup=breakup,
            state={
                "walletBalance": round(closing_balance, 2),
                "arrearBalance": round(ctx.consumer.arrear_balance, 2)
            }
        )
