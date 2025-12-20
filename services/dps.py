class DPSService:
    def calculate_daily_dps(self, arrear, monthly_rate):
        if arrear <= 0:
            return 0
        return arrear * (monthly_rate / 30)
