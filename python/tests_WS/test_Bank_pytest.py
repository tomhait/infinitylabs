import pytest
from Bank import BankAccount

@pytest.fixture
def account():
    return BankAccount(id=123456789)

def test_initial_balance(account):
    assert account.balance == 0

def test_deposit(account):
    account.deposit(1000)
    assert account.balance == 1000

def test_withdraw_success(account):
    account.deposit(1000)
    result = account.withdraw(500)
    assert result is True
    assert account.balance == 500

def test_withdraw_insufficient_funds(account):
    # This is why your current test is failing
    result = account.withdraw(500)
    assert result is False
    assert account.balance == 0

""" To run pytest in Bash:
    pytest test_Bank_pytest.py
"""