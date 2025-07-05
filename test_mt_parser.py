import unittest
from mt_parser import MT103Parser, MT202Parser, MT940Parser, MT900910Parser

class TestMTParsers(unittest.TestCase):
    def test_mt103_parser(self):
        msg = '20:REF123;32A:210101USD1000,00;50K:/12345678;59:/87654321;'
        parser = MT103Parser(msg)
        self.assertEqual(parser.get_transaction_reference(), 'REF123')
        self.assertAlmostEqual(parser.get_amount(), 1000.00)

    def test_mt202_parser(self):
        msg = '20:REF202;21:RELREF;32A:210101USD5000,00;58A:BANKBIC;'
        parser = MT202Parser(msg)
        self.assertEqual(parser.get_transaction_reference(), 'REF202')
        self.assertEqual(parser.get_related_reference(), 'RELREF')
        self.assertAlmostEqual(parser.get_amount(), 5000.00)
        self.assertEqual(parser.get_beneficiary_institution(), 'BANKBIC')

    def test_mt940_parser(self):
        msg = '25:123456789;28C:00001/001;60F:C210101USD1000,00;62F:C210131USD1500,00;'
        parser = MT940Parser(msg)
        self.assertEqual(parser.get_account_id(), '123456789')
        self.assertEqual(parser.get_statement_number(), '00001/001')
        self.assertEqual(parser.get_opening_balance(), 'C210101USD1000,00')
        self.assertEqual(parser.get_closing_balance(), 'C210131USD1500,00')

    def test_mt900910_parser(self):
        msg = '32A:210101USD2000,00;61:D210101USD2000,00;'
        parser = MT900910Parser(msg)
        self.assertAlmostEqual(parser.get_amount(), 2000.00)
        self.assertEqual(parser.get_debit_credit_advice(), 'D210101USD2000,00')

if __name__ == '__main__':
    unittest.main()
