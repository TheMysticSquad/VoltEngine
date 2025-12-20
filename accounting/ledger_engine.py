from models.ledger import LedgerEntry

class LedgerEngine:

    def __init__(self):
        self.entries = []

    def record(self, date, entry_type, amount, balance):
        entry = LedgerEntry(date, entry_type, amount, balance)
        self.entries.append(entry.as_dict())

    def snapshot(self):
        return self.entries
