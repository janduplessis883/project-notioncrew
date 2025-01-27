#!/usr/bin/env python
# coding=utf-8

from smolagents import CodeAgent, tool
from smolagents.models import HfApiModel


# Define custom tools for basic math operations
@tool
def add(a: float, b: float) -> float:
    """
    Adds two numbers.

    Args:
        a (float): The first number.
        b (float): The second number.

    Returns:
        float: The sum of a and b.
    """
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """
    Subtracts the second number from the first.

    Args:
        a (float): The first number.
        b (float): The second number.

    Returns:
        float: The result of a - b.
    """
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """
    Multiplies two numbers.

    Args:
        a (float): The first number.
        b (float): The second number.

    Returns:
        float: The product of a and b.
    """
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """
    Divides the first number by the second.

    Args:
        a (float): The first number.
        b (float): The second number.

    Returns:
        float: The result of a / b.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b


# Initialize the CodeAgent with the custom tools
agent = CodeAgent(
    tools=[add, subtract, multiply, divide],  # Add the custom tools
    model=HfApiModel(),  # Use Hugging Face's inference API
    verbose=True,  # Enable verbose logging for debugging
)

# Define the task for the agent
task = """
Solve the following math problem step by step:
1. Add 5 and 3.
2. Multiply the result by 4.
3. Subtract 10 from the result.
4. Divide the result by 2.
"""

# Run the agent
result = agent.run(task)

# Print the final result
print("Final Answer:")
print(result)
