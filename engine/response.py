class BillingResponse:
    def __init__(self, billing_type, amount, breakup, state):
        self.billing_type = billing_type
        self.amount = round(amount, 2)
        self.breakup = breakup
        self.state = state

    def to_json(self):
        return {
            "billingType": self.billing_type,
            "amount": self.amount,
            "breakup": self.breakup,
            "state": self.state
        }
