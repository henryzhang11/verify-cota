from logger_setup import setup_logging
# Initialize logging early in the application
setup_logging("find_mistake")
import logging
from model import VertexAI 
import verification
# Get a logger for the main module
logger = logging.getLogger(__name__)

def read_sentences(file, number):
    with open(file, 'r') as fin:
        content = fin.read()
    sep = '-' * 80
    raw_paras = content.split(sep)
    paragraphs = [p.strip() for p in raw_paras if p.strip()]
    paragraphs = paragraphs[20:20 + number]
    sep2 = '*'*80
    pairs = [p.split(sep2) for p in paragraphs]
    result = []
    for i in range(len(pairs)):
        temporary_problem = [sentence.strip() for sentence in pairs[i][0].splitlines() if sentence.strip()]
        temporary_solution = [sentence.strip() for sentence in pairs[i][1].splitlines() if sentence.strip()]
        result.append([temporary_problem, temporary_solution])
    return result

def test_find_first_mistake(problem_sent, solution_sent):
    model = VertexAI("focus-heuristic-454302-d2", "us-central1")
    verifier = verification.VerifyCotTheorems()
    verifier.solution_sentences = solution_sent
    verifier.problem_sentences = problem_sent
    verifier.all_sentences = problem_sent + solution_sent
    logger.info('-'*100)
    logger.info(f"Processing {problem_sent}")
    mistake_indices = verifier.find_first_mistake(model.generate)
    logger.info(f"{problem_sent}: {mistake_indices}")
    return mistake_indices

if __name__ == "__main__":
    sentences_list = read_sentences("clean_sentences_2.txt", 30)
    result = []
    for sentences in sentences_list:
        indices = test_find_first_mistake(sentences[0], sentences[1])
        with open("partial_result.txt", "a") as file:
            file.write('-'*80)
            file.write('\n')
            file.write(f'{sentences}\n')
            file.write('*'*80)
            file.write('\n')
            file.write(f'{indices}\n')
        result.append(indices)
    logger.info(f"result={result}")
