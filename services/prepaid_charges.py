from services.slab_tariff import SlabTariffCalculator

class PrepaidChargeService:

    def calculate_daily(self, meter, tariff, period):
        slab_calc = SlabTariffCalculator()

        energy, slab_breakup = slab_calc.calculate(
            meter.daily_units,
            tariff.slabs
        )

        fixed = tariff.fixed_charge / period.days
        duty = energy * tariff.duty_rate

        total = energy + fixed + duty

        return total, {
            "energy": energy,
            "fixed": fixed,
            "duty": duty,
            "slabs": slab_breakup
        }
