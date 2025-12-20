class TariffChange:

    @staticmethod
    def split(days, change_day):
        return {
            "oldTariffDays": change_day - 1,
            "newTariffDays": days - (change_day - 1)
        }
