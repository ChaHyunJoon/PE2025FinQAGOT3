# fin_server.py
from mcp.server.fastmcp import FastMCP
from datetime import datetime
import re
from typing import Optional
import numpy as np

mcp = FastMCP("Fin")

@mcp.tool()
def calculate_eps(net_income: float, outstanding_shares: int) -> float:
    """Calculate the EPS of the company using net income and outstanding shares."""
    if outstanding_shares == 0:
        raise ValueError("Outstanding shares cannot be zero.")
    return net_income / outstanding_shares

@mcp.tool()
def calculate_operating_profit_margin(operating_profit: float, sales: float) -> float:
    """Calculate the operating profit margin of the company using operating income and net sales."""
    if sales == 0:
        raise ValueError("Net sales cannot be zero.")
    return operating_profit / sales

@mcp.tool()
def calculate_cashflowfromoperations(net_income: float, non_cash_items: float, changes_in_working_capital: float):
  """Calculate the cash flow from operations of the company using net income, non cash items and change in working capital

   Args:
        net_income: Net income value of the company
        non_cash_items: Financial transactions or events that are recorded in a company's financial statements but do not involve the exchange of cash
        changes_in_working_capital: Difference in a company's working capital between two reporting periods

    Returns:
        Value of cash flow from operations
  """
  if (net_income is None) or (non_cash_items is None) or (changes_in_working_capital is None):
    print("Give me the net income, non cash items and change in working capital data first")
    return None

  return net_income + non_cash_items + changes_in_working_capital

@mcp.tool() 
def calculate_securities_value(securities: float, outstanding_shares: int) -> float:
    """Calculate the value of securities held by the company."""
    if outstanding_shares <= 0:
        raise ValueError("Outstanding shares must be greater than zero.")
    return securities * outstanding_shares

@mcp.tool()
def calculate_outstanding_shares(securities: float, securities_value: float) -> float:
    """Calculate the number of outstanding shares of the company."""
    if securities_value <= 0:
        raise ValueError("Securities value must be greater than zero.")
    return securities / securities_value

@mcp.tool()
def total_value_of_securities(securities_value: float, number_of_securities: int) -> float:
    """Calculate the total value of securities held by the company."""
    if securities_value < 0 or number_of_securities < 0:
        raise ValueError("Securities value and number of securities cannot be negative.")
    return securities_value * number_of_securities
    """Calculate the total value of long-term securities held by the company."""
    if short_term_securities < 0 or bonds < 0 or long_term_securities < 0:
        raise ValueError("Short-term securities, bonds, and long-term securities cannot be negative.")
    return short_term_securities + bonds + long_term_securities

@mcp.tool()
def calculate_total_dividends(per_share_dividend: float, outstanding_shares: float) -> float:
    """
    Calculate total cash dividends paid by the company.

    Args:
        per_share_dividend (float): Dividend paid per share.
        outstanding_shares (float): Total number of shares outstanding.

    Returns:
        float: Total cash dividends.
    """
    if per_share_dividend < 0 or outstanding_shares < 0:
        raise ValueError("Dividend and outstanding shares must be non-negative.")

    total_dividends = per_share_dividend * outstanding_shares
    return total_dividends

@mcp.tool()
def calculate_outstanding_shares_from_dividends(total_dividends: float, per_share_dividend: float) -> float:
    """Calculate outstanding shares using total dividends and per-share dividend."""
    if per_share_dividend <= 0:
        raise ValueError("Per-share dividend must be greater than zero.")
    return total_dividends / per_share_dividend

@mcp.tool()
def calculate_decrease_in_tax_positions(previous_additions: float, current_additions: float) -> float:
    """
    Calculate the decrease in additions for tax positions.

    Args:
        previous_additions (float): Additions in prior year.
        current_additions (float): Additions in current year.

    Returns:
        float: Decrease value (positive if decreased).
    """
    return previous_additions - current_additions

@mcp.tool()
def calculate_tax_position_change_rate(current_year_amount: float, previous_year_amount: float) -> float:
    """
    Calculate the percentage change in tax positions from the previous year.

    Args:
        current_year_amount (float): Tax positions in the current year.
        previous_year_amount (float): Tax positions in the previous year.

    Returns:
        float: Percentage change ((current - previous) / previous * 100).
    """
    if previous_year_amount == 0:
        raise ValueError("Previous year amount cannot be zero.")
    change_rate = ((current_year_amount - previous_year_amount) / previous_year_amount) * 100
    return change_rate

@mcp.tool()
def calculate_tax_position_to_net_income_ratio(tax_position_amount: float, net_income: float) -> float:
    """
    Calculate the ratio of tax positions to net income.

    Args:
        tax_position_amount (float): Tax positions amount.
        net_income (float): Net income.

    Returns:
        float: Percentage ratio.
    """
    if net_income == 0:
        raise ValueError("Net income cannot be zero.")
    ratio = (tax_position_amount / net_income) * 100
    return ratio

@mcp.tool()
def calculate_tax_position_to_total_tax_expense_ratio(tax_position_amount: float, total_tax_expense: float) -> float:
    """
    Calculate the ratio of tax positions to total tax expense.

    Args:
        tax_position_amount (float): Tax positions amount.
        total_tax_expense (float): Total tax expense.

    Returns:
        float: Percentage ratio.
    """
    if total_tax_expense == 0:
        raise ValueError("Total tax expense cannot be zero.")
    ratio = (tax_position_amount / total_tax_expense) * 100
    return ratio

@mcp.tool()
def calculate_unvested_awards_value(unvested_units: float, weighted_avg_fair_value: float) -> float:
    """
    Calculate total value of unvested restricted stock and performance awards at the weighted-averagegrant-datefair value

    Args:
        unvested_units (float): Number of unvested units.
        weighted_avg_fair_value (float): Weighted average grant-date fair value per unit.

    Returns:
        float: Total value (typically in thousands).
    """
    return unvested_units * weighted_avg_fair_value

@mcp.tool()
def calculate_total_long_term_securities(bonds: float, long_term_notes: float, other_securities: float = 0.0) -> float:
    """
    Calculate total value of issuable long-term securities.

    Args:
        bonds (float): Value of bonds.
        long_term_notes (float): Value of long-term notes.
        other_securities (float): Value of other long-term securities (optional).

    Returns:
        float: Total value.
    """
    return bonds + long_term_notes + other_securities

@mcp.tool()
def calculate_interest_expense_income_ratio(interest_expense: float, interest_income: float) -> float:
    """
    Calculate the ratio of interest expense to interest income.

    Args:
        interest_expense (float): Total interest expense.
        interest_income (float): Total interest income.

    Returns:
        float: Expense-to-income ratio.
    """
    if interest_income == 0:
        raise ValueError("Interest income cannot be zero.")
    return np.abs(interest_expense / interest_income)

@mcp.tool()
def calculate_unissued_approved_securities(approved_value: float, issued_value: float) -> float:
    """
    Calculate the value of approved but not yet issued securities.

    Args:
        approved_value (float): Total approved value.
        issued_value (float): Value already issued.

    Returns:
        float: Remaining approved but unissued value.
    """
    return approved_value - issued_value

@mcp.tool()
def calculate_long_term_component(long_term_liabilities: float, total_liabilities: float) -> float:
    """Calculate long-term component ratio."""
    if total_liabilities == 0:
        raise ValueError("Total liabilities cannot be zero.")
    return long_term_liabilities / total_liabilities

@mcp.tool()
def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
    """
    Calculate the current ratio, using the current assets and the current liabilities of that specific year.

    Parameters:
    - current_assets (float): Total current assets of the company.
    - current_liabilities (float): Total current liabilities of the company.

    Returns:
    - float: The current ratio. Returns float('inf') if current liabilities are 0.
    """
    if current_liabilities == 0:
        return float('inf')  # Infinite liquidity if no shortterm obligations
    return current_assets / current_liabilities



if __name__ == "__main__":
    mcp.run(transport="stdio")
