from engine.billing_engine import BillingEngine
from engine.context import BillingContext
from strategies.prepaid import PrepaidBilling
from models.consumer import Consumer
from models.meter import Meter
from models.tariff import Tariff
from models.period import Period

slabs = [
    {"upto": 50, "rate": 3},
    {"upto": 100, "rate": 4.5},
    {"upto": None, "rate": 6}
]

consumer = Consumer(
    consumer_id="C1001",
    wallet_balance=500,
    arrear_balance=1200,
    installment={"daily": 20},
    load_kw=2
)

meter = Meter(daily_units=6)
tariff = Tariff(
    slabs=slabs,
    fixed_charge=120,
    duty_rate=0.05
)

period = Period(days=30)

ctx = BillingContext(consumer, meter, tariff, period)

engine = BillingEngine(PrepaidBilling())
result = engine.run(ctx)

print(result.to_json())
