"""Example module to demonstrate the pre-commit hook agent."""


import os
import json
from typing import Optional


def greet(name):
 print(f"Hello, {name}!")


def add_numbers(a: int, b: int) -> int:
 """Add two numbers together."""
 return a + b


def calculate_total(items: list[int]) -> int:
 """Calculate the total of a list of numbers."""
 return sum(items)
