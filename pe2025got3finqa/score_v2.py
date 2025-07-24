from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
import os
from collections import defaultdict
_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, api_key=OPENAI_API_KEY)

with open('./data/qa_dict_diff.json', 'r') as f:
    qa_dict_diff = json.load(f)

with open('./data/results.json', 'r') as f:
    results = json.load(f)

# Build question → item and question → result lookup
qa_dict_map = {item['Question']: item for item in qa_dict_diff}
results_map = {item['Question']: item for item in results}

score_answer_prompt = PromptTemplate(
    input_variables=["question", "answer", "response"],
    template="""
    You have to score the response by comparing with the answer.
    You should score 0 or 1 as JSON with "score" key.
    You can ignore minor difference with the unit or numerical value.
    When comparing the numerical values, treat values as matching if they are approximately equal, allowing for rounding or minor decimal differences (for example, 18.698 ≈ 18.7 ≈ 18.70).
    Only give a score of 0 if the numerical meaning is fundamentally wrong or missing.
    Question: {question}
    Answer: {answer}
    Response: {response}
    Score:

    Output JSON: {{
      "score": 1 if the response correctly includes the meaning and approximate value of the answer, 0 if the response is fundamentally incorrect or missing the key information.
    }}
    """
)

class Score(BaseModel):
    """Score of the response"""
    score: int = Field(description="score of the response")

score_answer_chain = score_answer_prompt | llm.with_structured_output(Score)

correct = 0
evaluated = 0
results_with_score = []

# NEW: per-level tracking
level_correct = defaultdict(int)
level_total = defaultdict(int)

for question, qa_item in qa_dict_map.items():
    level_rating = qa_item.get('level_rating', 'N/A')
    #if level_rating!=3:
    #    continue
    if question not in results_map:
        print(f"⚠ Warning: No matching result for question → '{question[:50]}...'")
        continue

    result_item = results_map[question]
    response = result_item.get('Output', "")
    level_rating = qa_item.get('level_rating', 'N/A')

    try:
        score = score_answer_chain.invoke({
            'question': question,
            'answer': qa_item['Answer'],
            'response': response
        }).score
    except Exception as e:
        print(f"⚠ Error scoring question → '{question[:50]}...': {str(e)}")
        score = 0  # Fallback score on error

    correct += score
    evaluated += 1

    # Per-level tracking
    if isinstance(level_rating, int):
        level_correct[level_rating] += score
        level_total[level_rating] += 1

    # Prepare result entry with score and level_rating
    enriched_result = result_item.copy()
    enriched_result['Score'] = score
    enriched_result['level_rating'] = qa_item.get('level_rating', 'N/A')
    results_with_score.append(enriched_result)

accuracy = correct / evaluated if evaluated > 0 else 0.0
print(f"Overall Accuracy (evaluated {evaluated} questions): {accuracy:.4f}")

# NEW: print per-level accuracy
print("\nPer-Level Accuracy Report:")
for level in sorted(level_total.keys()):
    count = level_total[level]
    correct_count = level_correct[level]
    level_accuracy = correct_count / count if count > 0 else 0.0
    print(f"  Level {level}: {correct_count}/{count} correct → Accuracy: {level_accuracy:.4f}")

with open('./data/results_with_diff.json', 'w') as f:
    json.dump(results_with_score, f, indent=4)
    print(f"✅ Results with score saved to results_with_diff.json")
