class InstallmentService:
    def get_daily_installment(self, installment):
        if not installment:
            return 0
        return installment.get("daily", 0)
