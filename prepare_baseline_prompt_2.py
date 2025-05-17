from logger_setup import setup_logging
# Initialize logging early in the application
setup_logging("prepare_baseline")
import logging
from model import VertexAI
import verification
# Get a logger for the main module
logger = logging.getLogger(__name__)
import json
import re

quadruplets = []
jsonl_path = 'incorrect_solutions.jsonl'
with open (jsonl_path, 'r', encoding='utf-8') as fin:
    for line in fin:
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        quadruplets.append(entry)
quadruplets = quadruplets[10:]

exceptions = []
sentences = []
model = VertexAI(# Your project name, # Your project location)
for i in range(min(len(quadruplets), 50)):
    try:
        verifier = verification.VerifyCotTheorems()
        verifier.cleanup_answer(
            model.generate, 
            quadruplets[i]['problem'],
            quadruplets[i]['model_response']
        )
        sentences.append([verifier.problem_sentences, verifier.solution_sentences])
    except Exception as e:
        print(f"An error occured: {e}. ")
        sentences.append([[], []])
        exceptions.append(i)

with open("clean_sentences_2.txt", 'w') as fout:
    for sentence_list in sentences:
        fout.write("-"*80 + '\n')
        for sentence in sentence_list[0]:
            fout.write(sentence + '\n')
        fout.write("*"*80 + '\n')
        for sentence in sentence_list[1]:
            fout.write(sentence + '\n')

prompts_with_answer = []
for i in range(len(sentences)):
    all_sentences = sentences[i][0] + sentences[i][1]
    progress = ' '.join(f"({j + 1}) {s}" for j, s in enumerate(all_sentences))
    prompt = (
        f"Find the sentence number of the first sentence in the solution that makes a mistake in \"{progress}\". "
        f"For your reference, the correct answer is {quadruplets[i]['official_answer']}. "
        "Think before you answer. If the solution is correct, say -1."
    )
    prompts_with_answer.append(prompt)

prompts_without_answer = []
for i in range(len(sentences)):
    all_sentences = sentences[i][0] + sentences[i][1]
    progress = ' '.join(f"({j + 1}) {s}" for j, s in enumerate(all_sentences))
    prompt = (
        f"Find the sentence number of the first sentence in the solution that makes a mistake in \"{progress}\". "
        "Think before you answer. If the solution is correct, say -1."
    )
    prompts_without_answer.append(prompt)

with open("baseline_prompts_1.txt", 'w') as file:
    for prompt in prompts_without_answer:
        file.write("-"*80)
        file.write(f'\n{prompt}\n')

with open("baseline_prompts_2.txt", 'w') as file:
    for prompt in prompts_with_answer:
        file.write("-"*80)
        file.write(f'\n{prompt}\n')

print(f'exceptions occured at {list(quadruplets[i] for i in exceptions)}')

