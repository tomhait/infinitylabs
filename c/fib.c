#include <stdio.h>

// Function to calculate the nth Fibonacci number iteratively
long long fibonacci(int n) {
    if (n <= 1) {
        return n;
    }

    long long a = 0; // Represents the (n-2)th number
    long long b = 1; // Represents the (n-1)th number
    long long next_fib;

    for (int i = 2; i <= n; i++) {
        next_fib = a + b;
        a = b;
        b = next_fib;
    }

    return b;
}

int main() {
    int n;

    // Prompt the user for input
    printf("Enter the value of n (a non-negative integer): ");
    if (scanf("%d", &n) != 1 || n < 0) {
        printf("Invalid input. Please enter a non-negative integer.\n");
        return 1;
    }

    // Calculate the Fibonacci number
    long long result = fibonacci(n);

    // Print the result
    printf("The Fibonacci number at position %d is: %lld\n", n, result);

    return 0;
}

