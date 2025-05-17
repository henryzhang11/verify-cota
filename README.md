# Math Solution Verification Pipeline

A modular pipeline for loading math problems, generating and verifying solutions with a language model (Vertex AI), and identifying incorrect or logically flawed solution steps. Designed to work with the Hendrycks MATH benchmark.

---

## Table of Contents

- [Features](#features)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Usage](#usage)  
  - [1. Finding Incorrect Solutions](#1-finding-incorrect-solutions)  
  - [2. Finding First Mistake in a Solution](#2-finding-first-mistake-in-a-solution)  
  - [3. Preparing Baseline Prompts](#3-preparing-baseline-prompts)  
- [Module Details](#module-details)
  - [`paper.pdf`]
  - [`dataloader.py`](#dataloaderpy)  
  - [`verification.py`](#verificationpy)  
  - [`math_equivalence.py`](#math_equivalencepy)  
  - [`model.py`](#modelpy)  
  - [`logger_setup.py`](#logger_setuppy)  
  - [`find_incorrect_solution.py`](#find_incorrect_solutionpy)  
  - [`find_first_mistake.py`](#find_first_mistakepy)  
  - [`prepare_baseline_prompt_2.py`](#prepare_baseline_prompt_2py)  
- [Dependencies](#dependencies)  
- [License](#license)  

---

## Features

- **Data Loading**: Easily load the full MATH benchmark or hard (level 5 algebraic) subsets.  
- **Model Integration**: Wraps Google’s Vertex AI generative models for solution generation.  
- **Solution Checking**:  
  - Detects mismatches between generated and official answers (`MatchAnswer`).  
  - Identifies the first logically incorrect sentence in a student’s solution (`VerifyCotTheorems`).  
- **Math Equivalence**: String normalization to compare LaTeX expressions robustly.  
- **Logging**: Rotating, level‐separated console & file logging.  
- **Baseline Prompt Prep**: Cleans and formats data for few‐shot / baseline experiments.

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/yourusername/math-verification-pipeline.git
   cd math-verification-pipeline
    ```

2. **Set up a Python environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **Google Cloud**

   * In `model.py`, set your project and location:

     ```python
     os.environ['GOOGLE_CLOUD_PROJECT'] = "<YOUR_PROJECT_ID>"
     os.environ['GOOGLE_CLOUD_LOCATION'] = "<YOUR_REGION>"
     ```

2. **Logging**

   * Logs are written to `<module>.log` and rotated under `./log/` when they exceed 100 KB.

---

## Usage

### 1. Finding Incorrect Solutions

Generates solutions for a subset of MATH problems and records those that don’t match the official answer.

```bash
python find_incorrect_solution.py
```

* Output: `incorrect_solutions.jsonl` (one JSON per wrong solution).

### 2. Finding First Mistake in a Solution

Given a file of cleaned problem–solution sentence pairs (e.g. `clean_sentences_2.txt`), locates the first logically incorrect step.

```bash
python find_first_mistake.py
```

* Reads up to 50 entries from `clean_sentences_2.txt`.
* Logs the index of the first mistake for each pair.

### 3. Preparing Baseline Prompts

Transforms `incorrect_solutions.jsonl` into two text files of prompts for baseline experiments:

```bash
python prepare_baseline_prompt_2.py
```

* Outputs:

  * `clean_sentences_2.txt`
  * `baseline_prompts_1.txt` (no official answer)
  * `baseline_prompts_2.txt` (with official answer)

---

## Module Details

### `dataloader.py`

* **`load_MATH()`**
  Loads the full train split of the Hendrycks MATH benchmark.

* **`load_MATH_hard()`**
  Filters to level 5 non-geometry/non-precalculus problems, shuffles, and returns them.

* **`load_test_problem()`**
  Returns a single hard‐coded test problem.

---

### `verification.py`

* **`MatchAnswer`**

  * `evaluate_solution(problem, solution) → bool`
    Checks if the model’s `\boxed{...}` answer matches the official key using LaTeX normalization.

* **`VerifyCotTheorems`**

  * Parses, cleans, and categorizes solution sentences.
  * Applies and checks logical theorems step by step to find the first incorrect derivation.

---

### `math_equivalence.py`

Normalizes LaTeX‐style expressions (fractions, radicals, units, spacing) to compare model vs. ground‐truth answers.

---

### `model.py`

* Wraps Google Vertex AI generative models (`gemini-2.0-flash-001`, `gemini-2.5-flash-preview-04-17`).
* Provides `generate` and `leader_generate` methods with exponential‐backoff retries.

---

### `logger_setup.py`

* Configures a root logger with console (INFO) and file (DEBUG) handlers.
* Archives and clears log files exceeding 100 KB.

---

### `find_incorrect_solution.py`

* Loads up to `PROBLEM_NUMBERS` problems via `dataloader.load_MATH_hard()`.
* Prompts the model for each problem, extracts `\boxed{...}`, and uses `math_equivalence.is_equiv` to compare to the official answer.
* Writes mismatches to `incorrect_solutions.jsonl`.

---

### `find_first_mistake.py`

* Reads cleaned problem–solution pairs from `clean_sentences_2.txt`.
* For each pair, instantiates `VerifyCotTheorems` and calls `find_first_mistake()`.
* Logs the sentence index of the first logical error.

---
### `paper.pdf `

* Contains a summary of the project as a paper.

---

### `prepare_baseline_prompt_2.py`

* Loads `incorrect_solutions.jsonl`, cleans and punctuates solution text via `VerifyCotTheorems.cleanup_answer()`.
* Writes `clean_sentences_2.txt` and two sets of formatted prompts for baseline comparisons.

---

## Dependencies

Managed via `requirements.txt`:

```text
google-genai
spacy
datasets
google-cloud-aiplatform
```

Additional transitive dependencies include `vertexai`, `logging`, and standard Python libraries.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

```
```
