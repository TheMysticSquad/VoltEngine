class BillingContext:
    def __init__(self, consumer, meter, tariff, period):
        self.consumer = consumer
        self.meter = meter
        self.tariff = tariff
        self.period = period
