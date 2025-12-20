class InstallmentEngine:

    @staticmethod
    def revise(arrear_balance, tenure_days=180):
        if arrear_balance <= 0:
            return None

        return {
            "total": round(arrear_balance, 2),
            "daily": round(arrear_balance / tenure_days, 2),
            "tenureDays": tenure_days
        }

    @staticmethod
    def daily_amount(installment):
        return installment["daily"] if installment else 0
