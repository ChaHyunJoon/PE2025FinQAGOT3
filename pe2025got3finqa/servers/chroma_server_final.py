# chroma_server.py
from mcp.server.fastmcp import FastMCP
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from dotenv import load_dotenv, find_dotenv
import os
from typing import List, Dict

_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings = OpenAIEmbeddings(model='text-embedding-3-small',api_key=OPENAI_API_KEY)

from langchain_chroma import Chroma

docsearch = Chroma(
    persist_directory="./data/test_db",
    embedding_function=embeddings
)

mcp = FastMCP("Chroma")

import re

def extract_year(text):
    match = re.search(r'\b(19|20)\d{2}\b', text)
    return int(match.group()) if match else None

@mcp.tool()
def table_retrieval(question: str, ticker: str, target_year: int, focus: str = "", window: int = 1) -> List[Dict[str, str]]:
    """
    Retrieve the single best table data for Operating Profit Margin or current ratio.
    Only the table with score >= 1.02 and numerically closest to 1 is returned.
    """
    years = [target_year + i for i in range(-window, window + 2)]
    all_candidates = []

    for year in years:
        full_query = (
            f"Please provide detailed {focus} information. "
            f"Specifically, answer the following question: {question}. "
            f"The focus should remain on {focus} throughout."
        ) if focus else question

        # Retrieve tables with scores
        results_with_scores = docsearch.similarity_search_with_score(
            query=full_query,
            k=8,
            filter={
                "$and": [
                    {"company": {"$eq": ticker}},
                    {"fiscal": {"$eq": year}},
                    {"context_type": {"$eq": "table"}}
                ]
            }
        )

        for doc, score in results_with_scores:
            if score >= 1.02:
                extracted_year = extract_year(doc.page_content)
                all_candidates.append({
                    'year': extracted_year or year,
                    'content': doc.page_content,
                    'score': round(score, 4),
                    'rank': None,  # we will assign final rank after filtering
                    'doc_type': 'table'
                })

    # Select the table closest to score = 1
    if not all_candidates:
        return []  # no table meets the 1.02 threshold

    selected_table = min(
        all_candidates,
        key=lambda x: abs(x['score'] - 1)
    )
    selected_table['rank'] = 1  # assign final rank as 1

    return [selected_table]



@mcp.tool()
def broadened_year_retrieval(question: str, ticker: str, target_year: int, focus: str = "", window: int = 1) -> List[Dict[str, str]]:
    """
    Retrieve documents not only for the target year but also for surrounding years (±window).

    Returns:
        List[Dict[str, str]]: List of retrieved documents with 'year', 'content', 'score', 'rank'.
    """
    years = [target_year + i for i in range(-window, window + 2)]
    all_results = []

    for year in years:
        full_query = (
            f"Please provide detailed {focus} information. "
            f"Specifically, answer the following question: {question}. "
            f"The focus should remain on {focus} throughout."
        ) if focus else question

        # directly similarity_search_with_score
        results_with_scores = docsearch.similarity_search_with_score(
            query=full_query,
            k=8,
            filter={
                "$and": [
                    {"company": {"$eq": ticker}},
                    {"fiscal": {"$eq": year}}
                ]
            }
        )

        # allignment for higher scores
        sorted_results = sorted(results_with_scores, key=lambda x: x[1], reverse=True)

        for rank, (doc, score) in enumerate(sorted_results, start=1):
            extracted_year = extract_year(doc.page_content)
            all_results.append({
                'year': extracted_year or year,
                'content': doc.page_content,
                'score': round(score, 4),
                'rank': rank
            })

    return all_results

'''
@mcp.tool()
def table_retrieval(question: str, ticker: str, target_year: int, focus: str = "", window: int = 1) -> List[Dict[str, str]]:
    """
    Retrieve table data not only for the target year but also for surrounding years (±window).
    Use this tool only when the question contains Operating Profit Margin and current ratio.
    Returns:
        List[Dict[str, str]]: List of retrieved documents with 'year', 'content', 'score', 'rank'.
    """
    years = [target_year + i for i in range(-window, window + 2)]
    all_results = []

    for year in years:
        full_query = (
            f"Please provide detailed {focus} information. "
            f"Specifically, answer the following question: {question}. "
            f"The focus should remain on {focus} throughout."
        ) if focus else question

        # directly similarity_search_with_score
        results_with_scores = docsearch.similarity_search_with_score(
            query=full_query,
            k=8,
            filter={
                "$and": [
                    {"company": {"$eq": ticker}},
                    {"fiscal": {"$eq": year}},
                    {"context_type": {"$eq": "table"}}
                ]
            }
        )

        # allignment for higher scores
        sorted_results = sorted(results_with_scores, key=lambda x: x[1], reverse=True)

        for rank, (doc, score) in enumerate(sorted_results, start=1):
            extracted_year = extract_year(doc.page_content)
            all_results.append({
                'year': extracted_year or year,
                'content': doc.page_content,
                'score': round(score, 4),
                'rank': rank,
                'doc_type': 'table'
            })

    return all_results
'''
'''
@mcp.tool()
def broadened_year_retrieval(question: str, ticker: str, target_year: int, focus: str = "", window: int = 1) -> List[Dict[str, str]]:
    """
    Retrieve documents not only for the target year but also for surrounding years (±window).

    Args:
        question (str): The original question.
        ticker (str): Company ticker.
        target_year (int): The main fiscal year of interest.
        focus (str): Optional focus topic.
        window (int): How many years before/after to include.

    Returns:
        List[Dict[str, str]]: List of retrieved documents with 'year' and 'content'.
    """
    years = [target_year + i for i in range(-window, window+2)]
    all_results = []

    for year in years:
        full_query = (
            f"Please provide detailed {focus} information. "
            f"Specifically, answer the following question: {question}. "
            f"The focus should remain on {focus} throughout."
        ) if focus else question

        retriever = docsearch.as_retriever(search_kwargs={
            'k': 3,
            'filter': {
                "$and": [
                    {"company": {"$eq": ticker}},
                    {"fiscal": {"$eq": year}}
                ]
            }
        })

        results = retriever.invoke(full_query)
        for r in results:
            all_results.append({'year': year, 'content': r.page_content})

    return all_results
'''
'''
@mcp.tool()
def retrieve_factual_data(question:str, Symbol: str, fy: int, focus:str ="") -> str:
  """Search vector DB for the financial reports with the question and Symbol and fiscal year. It contains historical data for the company.

   Args:
        question: Question need to be answered
        Symbol: symbol of the company for filtering the documents
        fy: Fiscal year for filtering the documents
        focus: Optional focus area (e.g., 'working capital', 'net income').
    Returns:
        A related document for the question.
  """
  full_query = (f"Please provide detailed information about{focus}. "
        f"Specifically, answer the following question: {question}. "
        f"The focus should remain on {focus} throughout.") if focus else question
  retriever = docsearch.as_retriever(search_kwargs={'k': 3, 'filter':
  {
      "$and": [
          {
              "company": {
                  "$eq": Symbol
              }
          },
          {
              "fiscal": {
                  "$eq": fy
              }
          }
      ]
  }})
  result = retriever.invoke(full_query)
  if result:
    return result[0].page_content
  else:
    return "No data returned. Try again with correct Symbol and fiscal year, or different question"
'''

if __name__ == "__main__":
    mcp.run()
