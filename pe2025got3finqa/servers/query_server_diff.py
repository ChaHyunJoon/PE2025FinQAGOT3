#sqlite_server.py
#original src: https://github.com/hannesrudolph/sqlite-explorer-fastmcp-mcp-server/tree/main
from pathlib import Path
import sqlite3
import os
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from datetime import datetime
import re
# Initialize FastMCP server
mcp = FastMCP("SQLite Explorer",
    log_level="CRITICAL")

import sqlite3
from pathlib import Path

# Load company list from DB
DB_PATH = Path('./data/companies.db')

def load_company_list_from_db(db_path: str, table_name: str = 'companies', column_name: str = 'Security') -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT {column_name} FROM {table_name}")
        companies = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        companies = []
        print(f"Error loading companies: {e}")
    finally:
        conn.close()
    
    return companies

# Global company list loaded once
company_list = load_company_list_from_db(str(DB_PATH))

#def extract_companies(text: str) -> list:
#    """
#    Dummy company extractor. Ideally, this would use a proper NER model or regex.
#    For now, just example placeholder.
#    """
#    found = [c for c in company_list if c.lower() in text.lower()]
#    return found

def extract_companies(text: str, level_rating: int) -> list:
    if level_rating < 5:
        found = [c for c in company_list if c.lower() in text.lower()]
        return found

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    conditions = []
    
    # P/E ratio
    pe_match = re.search(r'P/E ratio (between|from)\s*(\d+)\s*(and|to)\s*(\d+)', text, re.IGNORECASE)
    if pe_match:
        pe_low, pe_high = float(pe_match.group(2)), float(pe_match.group(4))
        conditions.append(f'"P/E" BETWEEN {pe_low} AND {pe_high}')
    
    # Market cap
    mc_match = re.search(r'market cap (exceeding|over|greater than)\s*(\d+)\s*(billion|million)?', text, re.IGNORECASE)
    if mc_match:
        mc_value = float(mc_match.group(2))
        unit = mc_match.group(3)
        if unit and 'billion' in unit.lower():
            mc_value *= 1e9
        elif unit and 'million' in unit.lower():
            mc_value *= 1e6
        conditions.append(f'"Market cap" > {mc_value}')
    
    # Sector
    sector_match = re.search(r'(\w+ sector)', text, re.IGNORECASE)
    if sector_match:
        sector = sector_match.group(1).capitalize()
        conditions.append(f'Sector LIKE "%{sector}%"')
    
    # Founded year
    founded_match = re.search(r'founded in (\d{4})s', text, re.IGNORECASE)
    if founded_match:
        decade = int(founded_match.group(1))
        conditions.append(f'Founded BETWEEN {decade} AND {decade + 9}')

    # Headquarters
    hq_match = re.search(r'headquartered in ([\w\s,]+)', text, re.IGNORECASE)
    if hq_match:
        location = hq_match.group(1).strip()
        conditions.append(f'"Headquarters Location" LIKE "%{location}%"')

    if not conditions:
        print("No conditions parsed; fallback to empty result.")
        return []

    where_clause = " AND ".join(conditions)
    query = f'SELECT Security FROM companies WHERE {where_clause}'

    try:
        cursor.execute(query)
        results = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        results = []
    finally:
        conn.close()

    return results


def extract_fiscal_years(text: str, level_rating: int) -> Dict[str, Any]:
    """
    Extract fiscal years and (if applicable) founded decade for company filtering.

    Returns:
        {
            'fiscal_years': [list of years],
            'founded_decades': [list of decades]  # only if level_rating >= 5
        }
    """
    current_year = datetime.now().year
    fiscal_years = set()
    founded_decades = set()

    # Always extract explicit years
    raw_years = re.findall(r'(FY)?(\d{4})', text)
    cleaned_years = [match[1] for match in raw_years]
    fiscal_years.update(cleaned_years)

    if level_rating >= 5:
        # Relative years: e.g., '6 years ago'
        relative_matches = re.findall(r'(\d+)\s+years?\s+ago', text, re.IGNORECASE)
        for match in relative_matches:
            past_year = current_year - int(match)
            fiscal_years.add(str(past_year))

        # Decade expressions: e.g., 'in the 1990s'
        decade_matches = re.findall(r'in the (\d{4})s', text, re.IGNORECASE)
        for match in decade_matches:
            founded_decades.add(int(match))  # just store 1990, not all years

    return {
        'fiscal_years': list(fiscal_years),
        'founded_decades': list(founded_decades)
    }
@mcp.tool()
def generate_subquestions(query: str, level_rating: int) -> List[str]:
    """Generate subquestions if multiple companies or fiscal years are detected in the query.
    
    Args:
        query: Main question or query text
        
    Returns:
        List of generated subquestions
    """
    if not query:
        raise ValueError("Query cannot be empty")

    companies = extract_companies(query, level_rating)
    year_info = extract_fiscal_years(query, level_rating)
    fiscal_years = year_info['fiscal_years']
    founded_decades = year_info['founded_decades']

    subquestions = []

    # Case 1: Multiple companies only
    if len(companies) > 1 and len(fiscal_years) <= 1:
        for company in companies:
            subq = f"For company {company}, {query}"
            subquestions.append(subq)

    # Case 2: Multiple fiscal years only
    elif len(fiscal_years) > 1 and len(companies) <= 1:
        for year in fiscal_years:
            subq = f"For fiscal year {year}, {query}"
            subquestions.append(subq)

    # Case 3: Both multiple companies and years (cross-product)
    elif len(companies) > 1 and len(fiscal_years) > 1:
        for company in companies:
            for year in fiscal_years:
                subq = f"For company {company} and fiscal year {year}, {query}"
                subquestions.append(subq)

    # Fallback: return original if no split needed
    else:
        subquestions.append(query)

    return subquestions

@mcp.tool()
def temporal_alignment_tool(question: str, level_rating: int, reference_date: Optional[str] = None) -> str:
    today = datetime.today() if reference_date is None else datetime.strptime(reference_date, "%Y-%m-%d")
    year_today = today.year

    def convert_relative(expr: str) -> str:
        match = re.match(r"(\d+)\s+years?\s+ago", expr)
        if match:
            years_ago = int(match.group(1))
            return str(year_today - years_ago)
        return expr

    modified_question = re.sub(r"\b\d+\s+years?\s+ago\b", lambda m: convert_relative(m.group()), question)

    # Optionally, future: level_rating ≥ 5 → add quarter, month parsing
    return modified_question


@mcp.tool()
def extract_query_targets(query: str, level_rating: int) -> Dict[str, Any]:
    company = extract_companies(query, level_rating)
    year_info = extract_fiscal_years(query, level_rating)
    target_years = year_info['fiscal_years']
    founded_decades = year_info['founded_decades']

    financial_terms = [
        'cashflow', 'Operating Profit Margin',
        'revenue', 'liabilities', 'interest',' rent', 'net income',
        'earnings', 'assets', 'stock shares', 'net losses',
        'long term component', 'long term securities', 'current ratio',
        'securities', 'sales', 'lease', 'tax positions'
    ]
    focus_found = [term for term in financial_terms if term.lower() in query.lower()]
    focus = focus_found[0] if focus_found else "Not found"
    if "current ratio" in focus:
        focus += ", assets and liabilities"
    if "Operating Profit Margin" in focus:
        focus += ", sales and operating profit"

    return {
        'company': company,             # list
        'target_years': target_years,   # list
        'focus': focus                  # str
    }


if __name__ == "__main__":
    #print("Run")
    mcp.run(transport="stdio")
