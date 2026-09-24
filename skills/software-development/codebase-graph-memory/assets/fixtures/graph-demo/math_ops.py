"""Synthetic, non-sensitive fixture for structural graph checks."""


def add(left: int, right: int) -> int:
    return left + right


def multiply(left: int, right: int) -> int:
    total = 0
    for _ in range(right):
        total = add(total, left)
    return total
