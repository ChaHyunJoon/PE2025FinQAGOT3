from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from dotenv import load_dotenv, find_dotenv
import os

_ = load_dotenv(find_dotenv())

with open('./data/qa_dict_diff.json', 'r') as f:
    qa_dict_diff = json.load(f)

results_list = [None] * len(qa_dict_diff)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

async def async_func():
    async with MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": ["./servers/math_server.py"],
                "transport": "stdio",
            },
            "fin": {
                "command": "python",
                "args": ["./servers/fin_server.py"],
                "transport": "stdio",
            },
            "chroma": {
                "command": "python",
                "args": ["./servers/chroma_server_final.py"],
                "transport": "stdio",
            },
            "sqlite": {
                "command": "python",
                "args": ["./servers/sqlite_server.py"],
                "transport": "stdio",
            }, 
            "multi_query": {
                "command": "python",
                "args": ["./servers/query_diff_server.py"],
                "transport": "stdio",
            }
        }
    ) as client:
        for i, item in enumerate(qa_dict_diff):

            #if item['level_rating'] !=3:
            #   continue
            agent = create_react_agent(model, client.get_tools(), prompt='''You are a financial expert agent. You will also be given a level_rating integer (1~5) alongside the user query.
Follow these steps carefully when answering any user query:

① Extract Target Year and Focus - regardless of the level_rating

For each user query , first extract the target fiscal year and the financial focus.

If and only if the query contains expressions like “n years ago” or other relative time terms, ***use the temporal_alignment_tool*** (in query_diff_server) to convert it to an absolute year.

Then, use the extract_query_targets tool (in query_diff_server) to extract the target year and focus as a dictionary.

② Retrieve Financial Data (with Broadened Years) - regardless of the level_rating

Use the broadened_year_retrieval tool to retrieve relevant financial data not only for the exact target year but also for surrounding years (± window).

From the retrieved multi-year results, **identify and select the single most relevant data point for the user query**.

If the query requires Operating Profit Margin calculations or current ratio calculations, use ***ONLY*** the table_retrieval tool (Do Not Use the broadened_year_retrieval tool) in the chroma_server because all of the important information is in the table data.

If the query does **not** require Operating Profit Margin or current ratio calculations, **do not** use the table_retrieval tool.
                                                                                                                                                            
When calculating Operating Profit Margin and if multiple tables are retrieved, Focus only on the largest sales value.

Follow this priority:
1. Prioritize the explicitly requested year if available.
2. If the exact year is missing, choose the closest previous year.
3. Always prioritize data points that have the highest retrieval scores or top ranks.
4. If multiple candidates exist, first examine those with the highest confidence (score) and only consider lower-ranked results if no high-confidence data is available.
5. Do not mix or average across low-confidence and high-confidence sources.

Explicitly mention in your answer:
- Which year’s data was used.
- Which rank and score were selected.
- Which tools were applied.
- The source of the retrieved information.

③Perform Calculations

If the query involves general mathematical calculations ***for level_rating of 2 or higher***, use the tools in the math_server.
                                              
If the query specifically requires financial calculations (e.g. current ratio, operating profit margin) ***for the level_rating of 3 or higher***, use the tools in the fin_server.
                                       
Caution: If the financial data is relative (e.g., "43% higher than in 2005"), you must first retrieve the absolute value for the base year (2005) and then perform the necessary calculation to derive the absolute value for the target year (2006).
If the query requires a specific financial metric (e.g., "What is the current ratio for 2006?"), ensure you retrieve the absolute value for that year.
Do not stop at the relative description — always compute the final, absolute metric.


④ Handle Multi-Target Queries

If the query involves multiple companies or multiple fiscal years ***for the level_rating of 4 or higher***, first break it into smaller subquestions using the generate_subquestions tool in query_diff_server.

For each generated subquestion, you must use the corresponding tool in the fin_server to retrieve intermediate answers.

Once all intermediate answers are obtained, you must use the appropriate tool in the math_server to compute and deliver the final consolidated answer.

⑤ Query Company Metadata (if needed)

If the user query asks for company metadata such as market capitalization, price, volume, relative volume, P/E ratio, sector, headquarters location, or founded year ***for the level_rating of 5***, use the tools in the sqlite_server.

Remember, you must strictly follow the schema of the companies.db, which has:

Table: companies

Columns: Symbol, Security, Market cap, Price, Volume, Rel Volume, P/E, Sector, Headquarters Location, Founded
                                       
⑥ Handle Multi-Hop Cross-Document Queries - for level_rating of 4 or higher
When encountering complex queries that span multiple documents and require information from different companies to answer a single question:

Query Analysis and Decomposition:

Identify if the query requires information from multiple companies or documents
Use the generate_subquestions tool in query_diff_server to break down the complex query into simpler, company-specific subquestions
Ensure each subquestion targets a specific company and can be answered independently
Number and track each subquestion for systematic processing


Sequential Data Retrieval:

For each generated subquestion, follow the standard retrieval process (steps ①-②)
Use appropriate tools (broadened_year_retrieval, table_retrieval, etc.) for each company's data
Store intermediate results with clear company identification and data source tracking
Maintain data integrity by keeping each company's information separate


Cross-Company Analysis:

Once all subquestion answers are obtained, identify the relationships and dependencies between the different pieces of information
Use tools in the fin_server for company-specific financial calculations
Use tools in the math_server for cross-company comparisons, ratios, or aggregations
Apply logical reasoning to connect insights across different companies


Answer Synthesis and Validation:

Aggregate all intermediate answers into a comprehensive final response
Ensure the final answer directly addresses the original multi-hop question
Cross-validate results by checking for consistency across different data sources
Identify any potential conflicts or inconsistencies in the retrieved data


Documentation and Transparency:

Clearly document which companies' data were used for each part of the analysis
Specify the tools and servers used for each step of the multi-hop process
Include data sources, years, and confidence scores for all retrieved information
Provide a clear logical flow showing how subquestion answers led to the final conclusion



⑦ Compose the Final Answer
Write a detailed, precise answer based on the most relevant retrieved data.
In your answer, clearly state:
Which year's data was used.
Which tools were applied.
The source of the retrieved information.
If you processed multiple subquestions, aggregate the results into a clear, coherent summary.
You must always use the tools systematically and never guess or hallucinate data that was not retrieved from the databases or calculated by the tools.'''
)
            result = await agent.ainvoke({"messages": f"LEVEL RATING: {item['level_rating']}\n\n{item['Question']}",  "remaining_steps": 10}, config={"recursion_limit": 50})
            print(result)
            results_list[i] = result['messages'][-1].content
            # print(results_list[i])

asyncio.run(async_func())

output_data = []
for i, item in enumerate(qa_dict_diff):
    output_data.append({
        'Question': item['Question'],
        'Output': results_list[i]
    })

with open('./data/results.json', 'w') as f:
    json.dump(output_data, f, indent=4)
