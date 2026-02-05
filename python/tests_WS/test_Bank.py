import unittest

from ..src.Bank import BankAccount

class TestBank(unittest.TestCase):
    def setUp(self):
        self.account = BankAccount("123456789")

    def test_deposit(self):
        self.assertTrue(self.account.deposit(1000))

    def test_withdraw(self):
        self.assertFalse(self.account.withdraw(2000))
        self.assertTrue(self.account.withdraw(500))

if __name__ == "__main__":
    unittest.main()
