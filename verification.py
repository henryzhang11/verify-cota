import logging
import re
import json
from math_equivalence import is_equiv

MAX_STEPS = 100

# Get a logger for this module
logger = logging.getLogger(__name__)

class MatchAnswer:
    
    def __init__(self):
        pass
    
    def evaluate_solution(self, problem, solution):
        answer_key = problem.get('answer', '').strip()
        # Use regex to find the content inside \boxed{...}
        match = re.search(r'\\boxed\{(.+?)\}', solution)
        if match:
            boxed_content = match.group(1).strip()
            if is_equiv(boxed_content, answer_key):
                return True
            else:
                return False
        return False

class VerifyCotTheorems:

    def __init__(self):
        self.problem_sentences = []
        self.solution_sentences = []
        self.all_sentences = []
        self.theorems_applied = []
        self.application_correctness = []
        self.application_relevance = []

    def parse_text(self, model, paragraph):
        instruction = (
            f"Place each sentence in the following text on its own line: \"{paragraph}\". "
            "Wrap your response with ```. "
        )
        logger.info(f"Prompt: {instruction}")
        response = model(instruction)
        logger.info(f"Model's response: {response}")
        if not response:
            logger.info("Doesn't get response from model.")
            return
        start_index = response.find("```")
        end_index = response.rfind("```")
        if start_index == -1 or end_index == -1 or start_index == end_index:
            logger.info("Bad position(s) of ```.")
            return
        solution = response[start_index + 3:end_index].strip()
        sentences = solution.splitlines()
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def cleanup_answer(self, model, problem, solution):
        instruction = (
            f"Rewrite the solution by embedding each equation in a complete sentence: \"{solution}\". "
            "Do not correct the solution, omit parts of the solution, or add to the solution. "
            "Wrap your response with ```. "
        ) 
        logger.info(f"Prompt sent to the model: {instruction}")
        response = model(instruction)
        logger.info(f"Model's response: {response}")
        if not response:
            logger.info("Doesn't get response from model.")
            return
        start_index = response.find("```")
        end_index = response.rfind("```")
        if start_index == -1 or end_index == -1 or start_index >= end_index:
            logger.info("Bad position(s) of ```.")
            return
        punctuated_solution = response[start_index + 3:end_index].strip()
        # Parse solution into list of sentences.
        logger.info("Parsing problem statement. ")
        problem_sentences = self.parse_text(model, problem)
        self.problem_sentences = problem_sentences
        logger.info(f"Parsing solution. ")
        solution_sentences = self.parse_text(model, punctuated_solution)
        self.solution_sentences = solution_sentences
        self.all_sentences = problem_sentences + solution_sentences

    def find_first_mistake(self, model):
        n = len(self.solution_sentences)
        self.theorems_applied = [[] for _ in range(n)]
        self.application_correctness = [[] for _ in range(n)]
        self.application_relevance = [""] * n
        result = []
        for i in range(min(len(self.solution_sentences), MAX_STEPS)):
            logger.info(f"Checking {i + len(self.problem_sentences) + 1}.")
            for attempt in range(1, 11):
                self.name_theorem(i, model)
                self.check_application(i, model)
                got_verdicts = bool(self.application_correctness[i])
                all_correct = got_verdicts and all(self.application_correctness[i])
                relation = self.application_relevance[i]
                if got_verdicts:
                    if all_correct and relation != 'neither':
                        if relation == 'contradict':
                            result.append(i + len(self.problem_sentences) + 1)
                        break
                    else:
                        logger.info(f"Not all correct or relation='neither'")
                else:
                    logger.info(f"No verdicts")
            else:
                result.append(i + len(self.problem_sentences) + 1)
        return result

    def name_theorem(self, index, model):
        # Identify premises and theorem(s) used in the sentence.
        n = len(self.problem_sentences) + index + 1 
        progress = ' '.join(f"{s}" for s in self.all_sentences[:n])
        prompt = (
            f"{progress} Now, let's: 1. prove or disprove exactly the previous sentence by applying one theorem/logical rule a time; "
            "2. clean up the proof and output ONE JSON object of the form "
            "\"```json{\"rule 1\": theorem/logical axiom applied, \"conclusion 1\": conclusion obtained, ... }```\". "
            f"Prove or disprove \"{self.all_sentences[n-1]}\" assuming previous sentences or go to jail for failing. "
            "Reason using natural language before outputing ONE JSON object or go to jail for failing. "
            "For suppositions, prove or disprove it doesn't contradict previous sentences or go to jail for failing. "
        ) 
        logger.info(f"Prompt: {prompt}")
        for i in range(5):
            response = model(prompt)
            if not response:
                logger.warning("Doesn't get response from model.")
                continue
            json_pattern = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
            matches = json_pattern.findall(response)
            if not matches:
                logger.warning("JSON not in response.")
                continue
            match = matches[-1]
            logger.info(f"Response: {response}")
            self.theorems_applied[index] = match
            return

 
    def check_application(self, index, model):
        n = len(self.problem_sentences) + index + 1
        progress = ' '.join(f"{s}" for s in self.all_sentences[:n])
        prompt = (
            f"{progress} "
            f"Now, let's check the proof \"{self.theorems_applied[index]}\"of the previous sentence: "
            "1. Check each rule n is a rigorous theorem, that all its premises are fulfilled, and that it implies conclusion n. "
            f"2. Check if the last conclusion restates or contradicts \"{self.all_sentences[n-1]}\". "
            "3. Clean up your analysis and output ONE JSON object: "
            "\"```json{\"rule 1\": true or false, ... \"relation\": 'restate'/'contradict'/'neither' }```\" "
            "Analyze using natural language before outputing ONE JSON object or go to jail for failing."
        )
        logger.info(f"Prompt: {prompt}")
        for i in range(5):
            model_response = model(prompt)
            if not model_response:
                logger.info(f"Doesn't receive model response for check_application.")
                continue
            pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(pattern, model_response, re.DOTALL)
            if not match:
                logger.info("JSON not in response.")
                continue
            response = match.group(1)
            try:
                parsed_response = json.loads(response)
            except json.JSONDecodeError:
                logger.info("Failed to parse JSON from LLM response.")
                continue
            all_verdicts = []
            j = 1
            while True:
                k_verdict = f"rule {j}"
                if k_verdict not in parsed_response:
                    break
                verdict = parsed_response[k_verdict]
                all_verdicts.append(verdict)
                j += 1
            if all_verdicts == []:
                logger.info("Couldn't find 'rule 1'.")
                continue
            self.application_correctness[index] = all_verdicts
            if ('relation' not in parsed_response or 
                parsed_response['relation'] not in ['restate', 'contradict', 'neither']):
                logger.info(f"'relation' field in response not properly formatted")
                continue
            logger.info(f"Model's response: {model_response}")
            self.application_relevance[index] = parsed_response['relation']
            return
