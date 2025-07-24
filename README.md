# prompt-engineering-2025spring-FinQA

Skeleton code repository for the Topic: Financial QA - MCP with Multiple Servers

**File list**
- data
  - test_db: Pre-built Chroma DB (Vector DB) for the test set of FinQA
  - companies.csv: Company information data which includes stock market status
  - companies.db: companies.csv stored in SQLite DB
  - qa_dict.json: QA set for the accuracy test, total 50 question and answer set 
- servers
  - chroma_server_final.py: MCP server for the Chroma DB, adding some tools for retrieving informations in chroma.db with different methods by question types.
  - fin_server.py: MCP server for financial calculations
  - math_server.py: MCP server for arithmetic calculations
  - sqlite_server.py: MCP server for the SQLite DB
  - query_server_diff.py: MCP server for decomposing and preprocessing input query
- mcp_client_final.py: MCP client, run this code to generate result for the questions, adjusting prompt accustomed to finQA questionsets.
- score_v2.py: Run this code for scoring the accuracy with your result 

## References
- https://modelcontextprotocol.io/tutorials/building-mcp-with-llms
- https://github.com/modelcontextprotocol/python-sdk
- https://github.com/hannesrudolph/sqlite-explorer-fastmcp-mcp-server/tree/main

## Requirements

```
uv >= 0.6.14, python >= 3.13
```

## Installation

```
$ uv venv
$ uv sync
```

## Set Environment

You should create a `.env` file in the root directory of the project. This file will contain your OpenAI API key.

```
OPENAI_API_KEY="[your_openai_api_key]"
```

## Run MCP Client and Get Accuracy

```
$ python mcp_client_final.py
$ python score_v2.py
```

### Pre-defined Tool Examples
This mcp server has 5 types of servers and each kind of servers have several tools for its own sake :)

- `calculate_eps(net_income: float, outstanding_shares: int)`: Calculate the EPS of the company using net income and outstanding share
   - **Arguments**:
      - net_income: Net income value of the company
      - outstanding_shares: Total stock held by the company's shareholders
   - **Returns**:
      - EPS value or None if there is no value for arguments

- `calculate_cashflowfromoperations(net_income: float, non_cash_items: float, changes_in_working_capital: float)`: Calculate the cash flow from operations of the company using net income, non cash items and change in working capital
   - **Arguments**:
      - net_income: Net income value of the company
      - non_cash_items: Financial transactions or events that are recorded in a company's financial statements but do not involve the exchange of cash
      - changes_in_working_capital: Difference in a company's working capital between two reporting periods
   - **Returns**:
      - Value of cash flow from operations

- `retrieve_factual_data(question:str, ticker: str, fy: int) -> str`: Search vector DB for the financial reports with the question and ticker and fiscal year
   - **Arguments**:
      - question: Question need to be answered
      - ticker: Ticker of the company for filtering the documents
      - fy: Fiscal year for filtering the documents
   - **Returns**:
      - A related document for the question.
