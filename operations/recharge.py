from operations.installment import InstallmentEngine

class RechargeOperation:

    @staticmethod
    def apply(consumer, amount, revise_installment=True):
        consumer.wallet_balance += amount

        if revise_installment:
            consumer.installment = InstallmentEngine.revise(
                consumer.arrear_balance
            )

        return {
            "walletBalance": consumer.wallet_balance,
            "installment": consumer.installment
        }
