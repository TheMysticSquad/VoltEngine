from tariff.slab import SlabCalculator
from operations.dps import DPSCalculator
from operations.installment import InstallmentEngine
from operations.excess_demand import ExcessDemandPenalty


class PrepaidDailyBilling:

    def run(self, consumer, meter, tariff, period, ledger, date):

        # -----------------------------
        # 1. DPS on Arrear
        # -----------------------------
        dps = DPSCalculator.daily(
            consumer.arrear_balance,
            tariff.dps_monthly_rate
        )
        consumer.arrear_balance += dps

        # -----------------------------
        # 2. Energy Charges (Slab Based)
        # -----------------------------
        slab_calc = SlabCalculator()
        energy, slab_breakup = slab_calc.calculate(
            meter.daily_units,
            tariff.slabs
        )

        fixed = tariff.fixed_charge / period.days
        duty = energy * tariff.duty_rate

        daily_charge = energy + fixed + duty

        # -----------------------------
        # 3. Excess Demand Penalty
        # -----------------------------
        excess_kw, excess_penalty = ExcessDemandPenalty.calculate(
            recorded_demand=meter.max_demand_kw,
            contract_demand=consumer.load_kw,
            demand_rate=tariff.demand_rate,
            multiplier=tariff.excess_demand_multiplier
        )

        # -----------------------------
        # 4. Installment Deduction
        # -----------------------------
        installment = InstallmentEngine.daily_amount(
            consumer.installment
        )
        consumer.arrear_balance -= installment

        # -----------------------------
        # 5. Total Wallet Deduction
        # -----------------------------
        total_deduction = (
            daily_charge +
            installment +
            excess_penalty
        )

        consumer.wallet_balance -= total_deduction

        # -----------------------------
        # 6. Ledger Entries (Audit Safe)
        # -----------------------------
        ledger.record(date, "ENERGY", energy, consumer.wallet_balance)
        ledger.record(date, "FIXED", fixed, consumer.wallet_balance)
        ledger.record(date, "DUTY", duty, consumer.wallet_balance)
        ledger.record(date, "DPS", dps, consumer.wallet_balance)

        if installment > 0:
            ledger.record(
                date, "INSTALLMENT_RECOVERY",
                installment, consumer.wallet_balance
            )

        if excess_penalty > 0:
            ledger.record(
                date, "EXCESS_DEMAND_PENALTY",
                excess_penalty, consumer.wallet_balance
            )

        # -----------------------------
        # 7. Response (Frontend Ready)
        # -----------------------------
        return {
            "totalDeduction": round(total_deduction, 2),
            "breakup": {
                "energy": round(energy, 2),
                "fixed": round(fixed, 2),
                "duty": round(duty, 2),
                "dps": round(dps, 2),
                "installment": round(installment, 2),
                "excessDemand": {
                    "excessKW": round(excess_kw, 2),
                    "penalty": round(excess_penalty, 2)
                },
                "slabs": slab_breakup
            },
            "state": {
                "walletBalance": round(consumer.wallet_balance, 2),
                "arrearBalance": round(consumer.arrear_balance, 2)
            }
        }
