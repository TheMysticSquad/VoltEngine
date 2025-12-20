class BillingEngine:
    def __init__(self, strategy):
        self.strategy = strategy

    def run(self, context):
        return self.strategy.calculate(context)
