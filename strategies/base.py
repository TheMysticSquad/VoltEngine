from abc import ABC, abstractmethod

class BillingStrategy(ABC):
    @abstractmethod
    def calculate(self, context):
        pass
