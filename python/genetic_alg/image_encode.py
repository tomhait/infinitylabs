import numpy as np
from PIL import Image, ImageDraw
from abstract_genetic_alg import GeneticAlgorithm

class ImageEvolver(GeneticAlgorithm):
    def __init__(self, target_path, num_triangles=50, pop_size=20):
        img = Image.open(target_path).convert('RGB')
        resized_img = img.resize((256, 256), Image.Resampling.LANCZOS)
        self.target = np.array(resized_img).astype(float)
        self.width, self.height = resized_img.size
        self.num_triangles = num_triangles
        self.pop_size = pop_size
        self.gene_size = 10

    def create_individual(self):
        return np.random.rand(self.num_triangles, self.gene_size)

    def decode_and_render(self, chromosome):
        canvas = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(canvas, 'RGBA')

        for gene in chromosome:
            coords = [(gene[0] * self.width, gene[1] * self.height),
                      (gene[2] * self.width, gene[3] * self.height),
                      (gene[4] * self.width, gene[5] * self.height)]
            color = tuple((gene[6:10] * 255).astype(int))
            draw.polygon(coords, fill=color)

        return np.array(canvas).astype(float)

    def selection(self, population, tournament_size = 2):
        p1, p2 = np.random.choice(len(population), tournament_size, replace=False)
        return population[p1], population[p2]

    def fitness(self, chromosome):
        rendered = self.decode_and_render(chromosome)
        mse = np.mean((self.target - rendered) ** 2)
        return -mse

    def crossover(self, p1, p2):
        point = np.random.randint(1, self.num_triangles)
        child = np.concatenate([p1[:point], p2[point:]])
        return child

    def mutate(self, chromosome, rate=0.05):
        mask = np.random.rand(*chromosome.shape) < rate
        chromosome[mask] = np.random.rand(np.sum(mask))
        return chromosome

    def run(self, generations=100, file_name = "result.png"):
        population = [self.create_individual() for _ in range(self.pop_size)]

        for gen in range(generations):
            population.sort(key=self.fitness, reverse=True)

            best_fitness = self.fitness(population[0])
            if gen % 100 == 0:
                print(f"Generation {gen} | Best MSE: {-best_fitness:.2f}")

            new_pop = population[:self.pop_size // 10]
            while len(new_pop) < self.pop_size:
                parent1, parent2 = self.selection(population)

                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_pop.append(child)

            population = new_pop

        population.sort(key=self.fitness, reverse=True)
        final_img = Image.fromarray(self.decode_and_render(population[0]).astype(np.uint8))
        final_img.save(file_name)



evolver = ImageEvolver(r"brain.jpg", num_triangles=300, pop_size=100)
evolver.run(generations=3000, file_name="brain_result.jpg")