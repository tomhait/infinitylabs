from abstract_genetic_alg import GeneticAlgorithm
import numpy as np
from datetime import datetime
from functools import wraps

rng = np.random.default_rng(42)

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

class GenKnapsack(GeneticAlgorithm):

    def __init__(self, items = None, capacity = 10, pop_size = 10, num_generations = 50, mutation_rate = 0.01):
        self.items = items
        self.capacity = capacity
        self.pop_size = pop_size
        self.num_generations = num_generations
        self.mutation_rate = mutation_rate

    def create_individual(self):
        return [rng.choice([0,1]) for _ in range(len(self.items))]

    def fitness(self, chromosome):
        total_weight = 0
        total_value = 0
        for i in range(len(chromosome)):
            if chromosome[i] == 1:
                total_weight += self.items[i][0]
                total_value += self.items[i][1]

        if total_weight > self.capacity:
            return 0
        return total_value

    def crossover(self, parent1, parent2):
        point = rng.integers(low = 1, high = len(self.items) - 1)
        child1 = np.concatenate([parent1[:point], parent2[point:]])
        child2 = np.concatenate([parent2[:point], parent1[point:]])
        return child1, child2

    def mutate(self, chromosome):
        for i in range(len(chromosome)):
            if rng.random() < self.mutation_rate:
                chromosome[i] = 1 if chromosome[i] == 0 else 0


    def selection(self, population): # Tournament
        offspring = rng.choice(population, 2)
        return max(offspring, key=self.fitness)

    @func_timer
    def run(self, items = None):
        if items is not None:
            self.items = items

        population = [self.create_individual() for _ in range(self.pop_size)]

        for gen in range(self.num_generations):
            new_population = []
            population.sort(key=self.fitness, reverse=True)
            new_population.append(population[0])

            while len(new_population) < self.pop_size:
                p1 = self.selection(population)
                p2 = self.selection(population)

                c1, c2 = self.crossover(p1, p2)
                self.mutate(c1)
                self.mutate(c2)

                new_population.extend([c1, c2])

            population = new_population[:self.pop_size]

        best = max(population, key=self.fitness)
        return best, self.fitness(best)

class DynamicKnapsack:
    def __init__(self, items = None, capacity = 10):
        self.items = items
        self.capacity = capacity

    @func_timer
    def run(self, items = None):
        if items is not None:
            self.items = items

        n = len(self.items)
        dp = np.zeros((n + 1, self.capacity + 1))

        for i in range(1, n + 1):
            for w in range(1, self.capacity + 1):
                current_weight = self.items[i - 1][0]
                current_value = self.items[i - 1][1]

                if current_weight <= w:
                    value_with_item = current_value + dp[i - 1][w - current_weight]
                    value_without_item = dp[i - 1][w]
                    dp[i][w] = max(value_with_item, value_without_item)
                else:
                    dp[i][w] = dp[i - 1][w]

        included_items = []
        w = self.capacity
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                included_items.append(i - 1)
                w -= self.items[i - 1][0]

        included_items.reverse()

        return included_items, dp[n][self.capacity]

if __name__ == "__main__":
    items = [(2, 10), (3, 20), (5, 30), (7, 40), (1, 10), (1, 15), (1, 10), (2, 15)]
    knapsack = GenKnapsack()
    res = knapsack.run(items)
    print(f"\nBest Solution: {"".join(map(str, res[0]))} ;  Total Value: {res[1]}")
    dyn_knapsack = DynamicKnapsack()
    res = dyn_knapsack.run(items)
    print(f"\nBest Dynamic Solution: {"".join(map(str, res[0]))} ;  Total Value: {res[1]}")