# TDS Projet 2 – Data Analyst Agent

## Installation

Install the required packages using `uv sync`

## Initialization

Create `.env` and add the following variables:

- `GEMINI_API_KEY`: Gemini API key

## Usage

Run the agent using `uv run flask --app tds_project.py run` for testing purpose

# Test

Create `question.txt` and `edges.csv` in the root directory and run

```bash
curl http://127.0.0.1:5000/api/ \                                                                
  -X POST \
  -F "questions.txt=@question.txt" -F "csv=@edges.csv"
```
