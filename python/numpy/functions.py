import numpy as np
from datetime import datetime
from functools import wraps
import math

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

@func_timer
def zero_list(n):
    return [0]*n

@func_timer
def zero_np(n):
    return np.zeros(n)

@func_timer
def add_const(arr: np.ndarray | list, val = 5):
    if isinstance(arr, list):
        return [x + val for x in arr]
    return arr + val

@func_timer
def dot_prod(arr1: np.ndarray | list, arr2: np.ndarray | list):
    if isinstance(arr1, list):
        return [arr2[i] * x for i, x in enumerate(arr1)]
    return arr1.dot(arr2)

@func_timer
def apply_exp(arr: np.ndarray | list):
    if isinstance(arr, list):
        return [math.exp(x) for x in arr]
    return np.exp(arr)

@func_timer
def concat(arr1: np.ndarray | list, arr2: np.ndarray | list):
    if isinstance(arr1, list):
        return arr1 + arr2
    return np.concatenate((arr1,arr2))

@func_timer
def print_elem(arr: np.ndarray | list):
    print(arr)

#############################################################
rng = np.random.default_rng(42)

def get_random_mat(shape: tuple | list):
    """ Generates a random integer matrix by shape
    and append a column of ones
    """
    mat = rng.integers(low=-20, high=20, size=shape)
    return np.append(mat, np.ones((shape[0], 1)), axis=1)

#############################################################

def get_central_part(mat: np.ndarray):
    """ Returns the central part of the metrix excluding the
    first and last quarters of rows and columns
    """
    shape = mat.shape
    n1 = shape[0] // 4
    n2 = n1 * 3
    n3 = shape[1] // 4
    n4 = n3 * 3
    return mat[n1:n2, n3:n4]

#############################################################

def standard_matrix(mat: np.ndarray, axis=0):
    """ Returns a standardized numpy matrix by columns
    (default; axis=0)
    """
    mean = np.nanmean(mat, axis=axis, keepdims=True)
    std = np.nanstd(mat, axis=axis, keepdims=True)
    stand_mat = (mat-mean) / std
    return stand_mat

#############################################################

def create_quadratic_ds(n_samples = 500, a = 1, b = 2, c = 1):
    """ Creates a dataset that follows a quadratic formula plus
    noise, consisting n_samples between -30 and 100
    """
    x = np.linspace(-30, 100, n_samples)
    y = a * x**2 + b * x + c
    noise = rng.normal(size=n_samples)
    return x, y + noise

#############################################################

def apply_ols_quad(x, y):
    mat = np.column_stack([x**2, x, np.ones(x.shape)])
    coefficients = np.linalg.inv(mat.T @ mat) @ mat.T @ y
    quadratic_model = np.poly1d(coefficients)
    y_pred = quadratic_model(x)
    print(f"Fitted coefficients (a, b, c): {coefficients}")
    return y_pred

#############################################################

def softmax(x, axis = None):
    """ Computes the softmax values of x"""
    x_max = np.max(x, axis=axis)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis)