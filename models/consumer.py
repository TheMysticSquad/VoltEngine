class Consumer:
    def __init__(
        self,
        consumer_id,
        wallet_balance,
        arrear_balance=0,
        installment=None,
        load_kw=1.0
    ):
        self.consumer_id = consumer_id
        self.wallet_balance = wallet_balance
        self.arrear_balance = arrear_balance
        self.installment = installment
        self.load_kw = load_kw
