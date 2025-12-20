class LoadChange:

    @staticmethod
    def apply(consumer, new_load_kw):
        old = consumer.load_kw
        consumer.load_kw = new_load_kw

        return {
            "oldLoad": old,
            "newLoad": new_load_kw
        }
