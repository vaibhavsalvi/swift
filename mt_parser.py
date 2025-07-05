
class MTMessageParser:
    """
    Base parser for SWIFT MT messages represented as key-value pairs separated by semicolons.
    Example input: '20:REFERENCE;32A:210101USD1000,00;50K:/12345678;59:/87654321;'
    """
    def __init__(self, message: str):
        self.message = message
        self.fields = self.parse_message(message)

    def parse_message(self, message: str) -> dict:
        result = {}
        pairs = [pair for pair in message.split(';') if pair.strip()]
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                result[key.strip()] = value.strip()
        return result

    def get_field(self, field: str):
        return self.fields.get(field)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.fields})"

# MT103 Parser
class MT103Parser(MTMessageParser):
    """Parser for MT103 messages."""
    def get_transaction_reference(self):
        return self.get_field('20')

    def get_amount(self):
        value = self.get_field('32A')
        if value:
            # Example: '210101USD1000,00' -> extract amount
            parts = value[6:].replace(',', '.')
            try:
                return float(parts)
            except ValueError:
                return None
        return None

# MT202 Parser
class MT202Parser(MTMessageParser):
    """Parser for MT202 messages."""
    def get_transaction_reference(self):
        return self.get_field('20')

    def get_related_reference(self):
        return self.get_field('21')

    def get_amount(self):
        value = self.get_field('32A')
        if value:
            parts = value[6:].replace(',', '.')
            try:
                return float(parts)
            except ValueError:
                return None
        return None

    def get_beneficiary_institution(self):
        return self.get_field('58A')

# MT940 Parser
class MT940Parser(MTMessageParser):
    """Parser for MT940 statement messages."""
    def get_account_id(self):
        return self.get_field('25')

    def get_statement_number(self):
        return self.get_field('28C')

    def get_opening_balance(self):
        return self.get_field('60F')

    def get_closing_balance(self):
        return self.get_field('62F')

# MT900/910 Parser
class MT900910Parser(MTMessageParser):
    """Parser for MT900/910 debit/credit advice messages."""
    def get_amount(self):
        value = self.get_field('32A')
        if value:
            parts = value[6:].replace(',', '.')
            try:
                return float(parts)
            except ValueError:
                return None
        return None

    def get_debit_credit_advice(self):
        return self.get_field('61')

# Example usage:
if __name__ == "__main__":
    mt103_msg = '20:REF123;32A:210101USD1000,00;50K:/12345678;59:/87654321;'
    mt103 = MT103Parser(mt103_msg)
    print("MT103:", mt103)
    print("Transaction Reference:", mt103.get_transaction_reference())
    print("Amount:", mt103.get_amount())

    mt202_msg = '20:REF202;21:RELREF;32A:210101USD5000,00;58A:BANKBIC;'
    mt202 = MT202Parser(mt202_msg)
    print("\nMT202:", mt202)
    print("Transaction Reference:", mt202.get_transaction_reference())
    print("Related Reference:", mt202.get_related_reference())
    print("Amount:", mt202.get_amount())
    print("Beneficiary Institution:", mt202.get_beneficiary_institution())

    mt940_msg = '25:123456789;28C:00001/001;60F:C210101USD1000,00;62F:C210131USD1500,00;'
    mt940 = MT940Parser(mt940_msg)
    print("\nMT940:", mt940)
    print("Account ID:", mt940.get_account_id())
    print("Statement Number:", mt940.get_statement_number())
    print("Opening Balance:", mt940.get_opening_balance())
    print("Closing Balance:", mt940.get_closing_balance())

    mt900_msg = '32A:210101USD2000,00;61:D210101USD2000,00;'
    mt900 = MT900910Parser(mt900_msg)
    print("\nMT900/910:", mt900)
    print("Amount:", mt900.get_amount())
    print("Debit/Credit Advice:", mt900.get_debit_credit_advice())
