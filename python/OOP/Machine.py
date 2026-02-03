from datetime import datetime
from abc import ABC, abstractmethod  # This library allow the use of abstraction


# Phase 1

class Machine(ABC):  # abstract class - implement the methods only in MachineType1/2 classes

    @abstractmethod
    def start_machine(self):
        """starts the machine"""
    pass


    @abstractmethod
    def stop_machine(self):
        """stops the machine"""
    pass


    @abstractmethod
    def get_rate(self):
        """returns the price per minute of the machine"""
    pass


    @abstractmethod
    def get_accumulated_price(self):
        """returns the accumulated price of the machine"""
    pass


    @abstractmethod
    def is_on(self):
        """return True if this machine is on"""
    pass


class MachineType1(Machine):
    def __init__(self, price = 2):
        self.rate = price
        self.is_on = False
        self.cur_tot_price = 0
        self.start_time = None

    def start_machine(self):
        """starts the machine, start_time is optional"""
        self.is_on = True
        self.start_time = datetime.now()

    def _get_cur_price(self, stop_time):
        if not self.is_on:
            return 0
        time_elapsed = stop_time - self.start_time
        total_minutes = time_elapsed.total_seconds() / 60
        return self.rate * total_minutes

    def stop_machine(self):
        """stops the machine, stop_time is optional"""
        if not self.is_on:
            print("Machine is already down")
            return None
        self.cur_tot_price += self._get_cur_price(datetime.now())
        self.is_on = False
        return None

    def get_rate(self):
        """returns the price per minute of the machine"""
        return self.rate


    def get_accumulated_price(self):
        """returns the accumulated price of the machine"""
        return self.cur_tot_price + self._get_cur_price(datetime.now())


    def is_on(self):
        """return True if this machine is on"""
        return self.is_on

    def __str__(self):
        return f"Type 1 Machine current cost: {self.get_accumulated_price()}"


class MachineType2(Machine):

    def __init__(self, price = 5):
        self.rate = price
        self.is_on = False
        self.cur_tot_price = 0
        self.start_time = None

    def start_machine(self):
        """starts the machine, start_time is optional"""
        self.is_on = True
        self.start_time = datetime.now()

    def _get_cur_price(self, stop_time):
        if not self.is_on:
            return 0
        time_elapsed = stop_time - self.start_time
        total_minutes = time_elapsed.total_seconds() / 60
        return self.rate * total_minutes

    def stop_machine(self):
        """stops the machine, stop_time is optional"""
        if not self.is_on:
            print("Machine is already down")
            return None
        self.cur_tot_price += self._get_cur_price(datetime.now())
        self.is_on = False
        return None

    def get_rate(self):
        """returns the price per minute of the machine"""
        return self.rate


    def get_accumulated_price(self):
        """returns the accumulated price of the machine"""
        return self.cur_tot_price + self._get_cur_price(datetime.now())


    def is_on(self):
        """return True if this machine is on"""
        return self.is_on

    def __str__(self):
        return f"Type 2 Machine current cost: {self.get_accumulated_price()}"



# Phase 2: Maintains a list of all machines and has a single method for calculating the total price from all machines
class Cloud:

    def __init__(self):
        self.machines = []


    def add_machine(self, machine):
        """adds a machine to the cloud"""
        self.machines.append(machine)


    def get_tot_price(self):
        """calculate the total price of all the machines in the cloud"""
        return sum([mach.get_accumulated_price() for mach in self.machines])


    def __len__(self):
        return len(self.machines)






