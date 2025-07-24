# math_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers"""
    return a / b

@mcp.tool()
def averaging(value1:float, value2:float) -> float:
    """Calculate the average of two numbers"""
    return (value1 + value2) / 2

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers"""
    return a - b

@mcp.tool()
def bigger(a: float, b: float) -> bool:
    """Check if a is bigger than b"""
    return a > b

@mcp.tool()
def ratio(a: float, b: float) -> float:
    """Calculate the ratio of a to b"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    mcp.run(transport="stdio")