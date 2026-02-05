import pytest
import time
from Machine import *

@pytest.fixture
def machine():
    """ Returns a type 1 Machine"""
    return MachineType1()

@pytest.fixture
def cloud():
    """ Returns a Cloud"""
    return Cloud()

# Machine tests

def test_machine_initial_state(machine):
    assert machine.is_active() == False
    assert machine.get_accumulated_price() == 0

def test_machine_pricing(machine):
    machine.start_machine()
    time.sleep(1)
    assert machine.get_accumulated_price() > 0
    machine.stop_machine()
    assert machine.is_active() == False

# Cloud tests

def test_cloud_price(cloud, machine):
    m = MachineType2()
    cloud.add_machine(machine)
    cloud.add_machine(m)

    assert len(cloud) == 2

    assert cloud.get_tot_price() == 0

    machine.start_machine()
    m.start_machine()

    time.sleep(1)

    assert cloud.get_tot_price() > 0

""" To run pytest in Bash:
    pytest test_Machine.py
"""