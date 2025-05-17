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
        self.categorization = []
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

    def categorize(self, model):
        categories = []
        for k in range(min(MAX_STEPS // 4, 7)):
            # Separate sentences that are repetition/plan/definition/hypothesis/theorem citing from derivation
            n = len(self.solution_sentences)
            solution = ' '.join(f"({i + 1}) {s}" for i, s in enumerate(self.solution_sentences[:n]))
            instruction = (
                f"For all {n} sentences: Analyze and decide whether it derives any new result or not"
                " (repeat existing results, cites a theorem, introduces a plan, introduces a definition, "
                f"or introduces a hypothesis) in \"{solution}\". "
                "After analyzing, write your decisions in this JSON format: {\"sentence 1\": <value>, ...}, "
                "where <value> should be only \"derivation\" or \"others\". "
                "'...' should be potentially categorization of other sentences."
            )
            response = model(instruction)
            if not response:
                logger.warning("Doesn't get response from model.")
                return
            pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(pattern, response, re.DOTALL)
            if not match:
                logger.warning("JSON not in response.")
                return
            response = match.group(1)
            try:
                parsed_response = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("Couldn't parse JSON.")
                return
            result = []
            for j in range(n):
                category = f'sentence {j + 1}'
                if category not in parsed_response:
                    logger.warning(f"Doesn't contain {j + 1}th category. ")
                if parsed_response[category] not in ['derivation', 'others']:
                    logger.warning(f"Categorization {j + 1} spelling mistake: {parsed_response[category]}.")
                result.append(parsed_response[category])
            categories.append(result)
        temp = categories
        categories = []
        for category in temp:
            if len(category) == n:
                categories.append(category)
        vote = []
        for i in range(len(categories[0])):
            n = 0
            for j in range(len(categories)):
                if categories[j][i] == 'derivation':
                    n += 1
            if n >= len(categories) // 2:
                vote.append('derivation')
            else:
                vote.append('others')
        self.categorization = vote
        
    def find_first_mistake(self, model):
        n = len(self.solution_sentences)
        self.theorems_applied = [[] for _ in range(n)]
        self.application_correctness = [[] for _ in range(n)]
        self.application_relevance = [""] * n
        self.categorize(model)
        result = []
        for i in range(min(len(self.solution_sentences), MAX_STEPS)):
            if self.categorization[i] == 'derivation':
                logger.info(f"Checking sentence {i + len(self.problem_sentences) + 1}.")
                self.name_theorem(i, model)
                self.check_application(i, model)
                got_verdicts = bool(self.application_correctness[i])
                all_correct = got_verdicts and all(self.application_correctness[i])
                is_original = self.application_relevance[i] == 'restate'
                if not (got_verdicts and all_correct and is_original):
                    logger.info(f"Found mistake at {i + len(self.problem_sentences) + 1}. ")
                    result.append(i + len(self.problem_sentences) + 1)
        return result
        
    def name_theorem(self, index, model):
        # TODO: ask model to check definitions along theorems if necessary
        # TODO: reductio ad absurdum slows down and distabilizes premise filtering.
        # Identify premises and theorem(s) used in the sentence.
        n = len(self.problem_sentences) + index + 1 
        progress = ' '.join(f"({i + 1}) {s}" for i, s in enumerate(self.all_sentences[:n]))
        prompt = (
            f"Sentences 1 to {n-1} are correct but sentence {n} might be incorrect; "
            "apply rules (general theorems/logical principles that have premises and a conclusion) one at a time "
            f"to refute or derive sentence {n} in \"{progress}\" (do not rederive sentence 1 to {n-1}; "
            f"do not stop until you refuted or derived exactly sentence {n} by applying one theorem at a time; "
            f"do not stop after you derived sentence {n} is 'not necessarily true/false', find out is it's true or false). "
            f"After applying rules to refute or derive sentence {n}, copy ALL applications of rules "
            f"logically necessary to refute or derive sentence {n}"
            "(rule used, indices of sentences used as premises to apply this rule, "
            "indices of previously copied conclusions used as premises to apply this rule, and the obtained conclusion) "
            "to only ONE JSON object with this format: "
            "\"```json{\"rule 1\": ALL premises and conclusion of the rule written in complete sentences, "
            "\"sentence numbers 1\": list of integers, \"conclusion numbers 1\": list of integers, "
            "\"conclusion 1\": result of application of the rule written as a complete sentence, ... }```\" "
            "with '...' being potentially other quadruplets of rule, sentence numbers, conclusion numbers, and conclusions. "
            f"Don't copy sentences 1 to {n-1} as rules or conclusions and list their sentence numbers if necessary. "
            "Don't copy sentences or previously copied conclusions to the \"rule i\" field. "
            f"Don't copy sentence {n} as a rule and then say sentence {n} is true by that rule. "
            "Don't use JSON keys other than \"rule i\", \"sentence numbers i\", \"conclusion numbers i\", and \"conclusion i\". " 
            "Don't copy incorrect applications and copy only a successful attempt. "
            f"Apply the rules in natural language and refute/derive sentence {n} before COPYING your results to JSON. "
        ) 
        logger.info(f"Prompt: {prompt}")
        for i in range(5):
            response = model(prompt)
            if not response:
                logger.warning("Doesn't get response from model.")
                continue
            pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(pattern, response, re.DOTALL)
            if not match:
                logger.warning("JSON not in response.")
                continue
            break
        logger.info(f"Response: {response}")
        response = match.group(1)
        self.theorems_applied[index] = response     
 
    def check_application(self, index, model):
        n = len(self.problem_sentences) + index + 1
        progress = ' '.join(f"({i + 1}) {s}" for i, s in enumerate(self.all_sentences[:n]))
        prompt = (
            f"Sentence 1 to {n-1} is correct, sentence {n} might be incorrect. "
            f"Check applications of each rule in ```{self.theorems_applied[index][1:-1].strip()}``` "
            f"that proves sentence {n} based on sentence 1 to {n-1} \"{progress}\". "
            "For every rule n, check that each of its premises is fulfilled and that it implies conclusion n "
            "(think before you give a verdict; you don't have to use every listed sentence/conclusion; "
            "go over sentences listed in \"sentence numbers n\" and \"conclusion numbers n\"). "
            f"Then decide if the last conclusion restates or contradicts (or neither restate nor contradicts) sentence {n}: "
            f"\"{self.all_sentences[n - 1]}\" (the last conclusion doesn't have to answer the question in the context; "
            f"compare the last conclusion with the sentence here instead of sentence {n-1}; "
            f"conclude 'restate' if the last conclusion says sentence {n} is correct/true/etc). "
            "After checking, copy your application correctness verdicts for all conclusions "
            "and your relation verdict for the last conclusion to one JSON object in this format: "
            "\"```json{\"verdict 1\": application 1's correctness (true or false), ... \"relation\": <value>}```\" "
            "with '...' being potentially other verdicts and <value> being 'restate', 'contradict', or 'neither'. "
            "Don't start writing JSON keys \"verdict i\" from any j bigger than 1."
            "Don't skip verdicts (copy application correctness verdicts for ALL conclusionsl). "
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
                k_verdict = f"verdict {j}"
                if k_verdict not in parsed_response:
                    break
                verdict = parsed_response[k_verdict]
                all_verdicts.append(verdict)
                j += 1
            if all_verdicts == []:
                logger.info("Couldn't find 'verdict 1'.")
                continue
            self.application_correctness[index] = all_verdicts
            if ('relation' not in parsed_response or 
                parsed_response['relation'] not in ['restate', 'contradict', 'neither']):
                logger.info(f"'relation' field in response not properly formatted")
                continue
            break
        logger.info(f"Model's response: {model_response}")
        self.application_relevance[index] = parsed_response['relation']
