class WalletService:
    def deduct(self, consumer, amount):
        consumer.wallet_balance -= amount
        return consumer.wallet_balance
