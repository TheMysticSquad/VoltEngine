class ExcessDemandPenalty:

    @staticmethod
    def calculate(recorded_demand, contract_demand, demand_rate, multiplier):
        """
        recorded_demand : Meter MD (kW/kVA)
        contract_demand : Sanctioned Load / Contract Demand
        """

        if recorded_demand <= contract_demand:
            return 0, 0

        excess = recorded_demand - contract_demand
        penalty = excess * demand_rate * multiplier

        return excess, round(penalty, 2)
