```python
def fibonacci_iterative(n):
    """
    Generate a list containing the first n Fibonacci numbers.

    Parameters:
    n (int): The number of Fibonacci numbers to generate. Should be non-negative.

    Returns:
    list: A list of the first n Fibonacci numbers.
    """
    if n < 0:
        # For negative input, return an empty list.
        return []
    elif n == 0:
        # When n is zero, return an empty list.
        return []
    elif n == 1:
        # When n is 1, return list with only the first Fibonacci number.
        return [0]
    elif n == 2:
        # When n is 2, return the first two Fibonacci numbers.
        return [0, 1]
    # For n > 2, generate subsequent Fibonacci numbers iteratively.
    fib_sequence = [0, 1]
    for i in range(2, n):
        next_fib = fib_sequence[-1] + fib_sequence[-2]
        fib_sequence.append(next_fib)
    return fib_sequence
```