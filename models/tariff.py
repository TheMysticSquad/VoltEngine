class Tariff:
    def __init__(
        self,
        slabs,                 # list of slab dicts
        fixed_charge,
        duty_rate=0.0,
        dps_monthly_rate=0.015
    ):
        self.slabs = slabs
        self.fixed_charge = fixed_charge
        self.duty_rate = duty_rate
        self.dps_monthly_rate = dps_monthly_rate
