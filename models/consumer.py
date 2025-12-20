class Consumer:
    def __init__(
        self,
        consumer_id,
        wallet_balance,
        arrear_balance=0,
        load_kw=1.0,
        installment=None
    ):
        self.consumer_id = consumer_id
        self.wallet_balance = wallet_balance
        self.arrear_balance = arrear_balance
        self.load_kw = load_kw
        self.installment = installment
