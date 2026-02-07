import pytest
import time
from Machine import *
from datetime import timedelta
from freezegun import freeze_time


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

def test_machine_pricing(machine, mocker):
    with freeze_time("2026-01-01 12:00:00") as frozen_datetime:
        machine.start_machine()
        frozen_datetime.tick(delta=timedelta(seconds=60))
        assert machine.get_accumulated_price() > 0
        print(machine.get_accumulated_price())
        machine.stop_machine()
        assert machine.is_active() == False


# Cloud tests

def test_cloud_price(cloud, machine, mocker):
    with freeze_time("2026-01-01 12:00:00") as frozen_datetime:

        m = MachineType2()
        cloud.add_machine(machine)
        cloud.add_machine(m)

        assert len(cloud) == 2

        assert cloud.get_tot_price() == 0

        machine.start_machine()
        m.start_machine()

        frozen_datetime.tick(delta=timedelta(seconds=60))

        assert cloud.get_tot_price() > 0
        print(cloud.get_tot_price())

""" To run pytest in Bash:
    pytest -s test_Machine.py
"""