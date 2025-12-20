class SlabCalculator:

    def calculate(self, units, slabs):
        remaining = units
        total = 0
        breakup = []

        for slab in slabs:
            if remaining <= 0:
                break

            limit = slab["upto"]
            rate = slab["rate"]

            slab_units = remaining if limit is None else min(remaining, limit)
            amount = slab_units * rate

            breakup.append({
                "units": slab_units,
                "rate": rate,
                "amount": amount
            })

            total += amount
            remaining -= slab_units

        return total, breakup
