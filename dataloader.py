import random
from datasets import load_dataset

def load_MATH():
    # Load the dataset from Hugging Face.
    math_problems = load_dataset("nlile/hendrycks-MATH-benchmark", split='train')
    # Convert the Dataset object to a list of dictionaries
    problems = [dict(item) for item in math_problems]
    return problems

def load_MATH_hard():
    # load the training split
    ds = load_dataset("nlile/hendrycks-MATH-benchmark", split="train")
    # filter for Level 5
    hard = ds.filter(lambda ex: ex["level"] == 5)
    algebraic = ds.filter(lambda ex: ex['subject'] != 'Geometry' and ex['subject'] != 'Precalculus')
    # pick one at random
    shuffled = algebraic.shuffle(seed=42)
    problems = [dict(item) for item in shuffled]
    return problems

def load_test_problem():
    return [{'problem': r'How many vertical asymptotes does the graph of $y=\frac{x+1}{(x+1)^2}$ have?'}]
