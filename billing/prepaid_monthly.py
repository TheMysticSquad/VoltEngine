class PrepaidMonthlyInvoice:

    def generate(self, consumer, ledger_entries, month):

        summary = {
            "energy": 0,
            "fixed": 0,
            "dps": 0,
            "installment": 0
        }

        for e in ledger_entries:
            if e["type"] in summary:
                summary[e["type"].lower()] += e["amount"]

        return {
            "consumerId": consumer.consumer_id,
            "month": month,
            "summary": summary,
            "closingWallet": consumer.wallet_balance,
            "closingArrear": consumer.arrear_balance
        }
