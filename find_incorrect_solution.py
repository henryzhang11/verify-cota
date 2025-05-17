import json
from model import VertexAI 
from dataloader import load_MATH_hard 
import re
from logger_setup import setup_logging
from math_equivalence import is_equiv
import logging
setup_logging("find_incorrect_solution")
logger = logging.getLogger(__name__)

PROBLEM_NUMBERS = 850
math_problems = load_MATH_hard() # or 'load_MATH' if testing on all problems
math_problems = math_problems[:PROBLEM_NUMBERS]
model = VertexAI(# Your project name, # Your project region)
incorrect_solutions = []

for idx, problem in enumerate(math_problems):
    bare_prompt = problem['problem']  # Use 'problem' key
    # TODO: if necessary, add the prompt "Please provide your final answer within \boxed{...}.".
    prompt = bare_prompt
    logger.info("-"*80)
    logger.info(f"Processing problem {idx + 1}/{len(math_problems)}: {prompt}")
    response = model.generate(prompt)
    logger.info("-"*40)
    logger.info(f"response = {response}")
    logger.info("-"*40)
    if not response:
        logger.info(f"Couldn't generate model response while processing problem {idx + 1}/{len(math_problems)}")
        continue
    answer_key = problem.get('answer', '').strip()
    start_tag = r'\boxed{'
    start = response.rfind(start_tag)
    if start == -1:
        logger.info(f"couldn't find boxed content solving problem {idx + 1}")
        continue
    start += len(start_tag)
    end = response.rfind('}')
    if end == -1 or end < start:
        logger.info(f"couldn't find boxed content solving problem {idx + 1}")
        continue
    boxed_content = response[start:end].strip()
    if not is_equiv(boxed_content, answer_key):
        incorrect_solutions.append({
            "problem": bare_prompt,
            "official_answer": answer_key,
            "model_answer": boxed_content,
            "model_response": response
        })

out_path = "incorrect_solutions.jsonl"
with open(out_path, "w", encoding="utf-8") as fout:
    for case in incorrect_solutions:
        fout.write(json.dumps(case, ensure_ascii=False) + '\n')
logger.info(f"Found and saved {len(incorrect_solutions)} incorrect solutions.")
