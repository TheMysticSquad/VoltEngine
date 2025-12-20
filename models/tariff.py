class Tariff:
    def __init__(
        self,
        slabs,
        fixed_charge,
        duty_rate=0.0,
        dps_monthly_rate=0.015,
        demand_rate=0.0,                 # ₹/kW or ₹/kVA
        excess_demand_multiplier=1.5     # Regulatory
    ):
        self.slabs = slabs
        self.fixed_charge = fixed_charge
        self.duty_rate = duty_rate
        self.dps_monthly_rate = dps_monthly_rate
        self.demand_rate = demand_rate
        self.excess_demand_multiplier = excess_demand_multiplier
