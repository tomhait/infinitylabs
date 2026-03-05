import numpy as np

rng = np.random.default_rng(42)

def flip():
    return rng.choice([0,1])

def biased_025():
    if flip() == 1 and flip() == 1:
        return 0
    return 1

def fair_three():
    while True:
        a = flip()
        b = flip()

        if a == 1 and b == 0:
            return 2
        if a == 0 and b == 1:
            return 1
        if a == 0 and b == 0:
            return 0

def biased_flip():
    return rng.choice([0, 1], p=[0.1,0.9])

def fair_flip():
    while True:
        a = biased_flip()
        b = biased_flip()
        if a != b:
            return a

n_steps = 1000
res = [biased_025() for i in range(n_steps)]
prob = sum(res)/len(res)
print(f"Probabilities of 0/1 are: {1-prob:.2f} {prob:.2f}")

res = np.array([fair_three() for i in range(n_steps)])
prob_1 = np.sum(res==1)/len(res)
prob_2 = np.sum(res==2)/len(res)
print(f"Probabilities of 0/1/2 are: {1-prob_1-prob_2:.2f} {prob_1:.2f} {prob_2:.2f}")

res = [fair_flip() for i in range(n_steps)]
prob = sum(res)/len(res)
print(f"Probabilities of 0/1 are: {1-prob:.2f} {prob:.2f}")
