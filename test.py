import voltengine

print(voltengine.__version__)

billing = voltengine.PrepaidDailyBilling()
ledger = voltengine.LedgerEngine()

print("VoltEngine loaded successfully")
