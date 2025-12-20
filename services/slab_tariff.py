class SlabTariffCalculator:

    def calculate(self, units, slabs):
        remaining = units
        energy_charge = 0
        breakup = []

        for slab in slabs:
            if remaining <= 0:
                break

            slab_limit = slab["upto"]
            rate = slab["rate"]

            if slab_limit is None:
                slab_units = remaining
            else:
                slab_units = min(remaining, slab_limit)

            slab_amount = slab_units * rate
            energy_charge += slab_amount

            breakup.append({
                "units": slab_units,
                "rate": rate,
                "amount": slab_amount
            })

            remaining -= slab_units

        return energy_charge, breakup
