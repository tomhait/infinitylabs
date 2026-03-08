from abc import ABC, abstractmethod

class GeneticAlgorithm(ABC):
    """ Abstract base class for |Genetic algorithm implementation"""

    @abstractmethod
    def fitness(self, chromosome):
        pass

    @abstractmethod
    def crossover(self, parent1, parent2):
        pass

    @abstractmethod
    def mutate(self, chromosome):
        pass

    @abstractmethod
    def selection(self, population):
        pass