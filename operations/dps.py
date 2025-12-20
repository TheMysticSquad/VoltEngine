class DPSCalculator:

    @staticmethod
    def daily(arrear, monthly_rate):
        if arrear <= 0:
            return 0
        return arrear * (monthly_rate / 30)
