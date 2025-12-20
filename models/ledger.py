class LedgerEntry:
    def __init__(self, date, entry_type, amount, balance):
        self.date = date
        self.entry_type = entry_type
        self.amount = amount
        self.balance = balance

    def as_dict(self):
        return {
            "date": self.date,
            "type": self.entry_type,
            "amount": round(self.amount, 2),
            "balance": round(self.balance, 2)
        }
