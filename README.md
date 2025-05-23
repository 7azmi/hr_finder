# Anymailfinder HR Email Finder

Batch HR decision-maker email retrieval via Anymailfinder API. Outputs to CSV.

## Repo Description

Python script leveraging Anymailfinder API for bulk HR email discovery from domain list, exporting to CSV.

## Features

*   Domain list processing (`domains.txt`).
*   Domain cleaning (strip scheme, `www.`, trailing slash).
*   Anymailfinder Decision Maker API integration (`hr` category).
*   Robust API error handling (timeouts, connections, API responses).
*   CSV output (`hr_emails_results_bulk.csv`) with structured results/errors.
*   API key via ENV var (`ANYMAILFINDER_API_KEY`) or prompt.

## Prerequisites

*   Python 3.6+
*   `requests` library (`pip install -r requirements.txt`)
*   Anymailfinder API Key

## Installation

```bash
git clone <repository_url>
cd hr_finder # or project root
pip install -r requirements.txt
```

## Setup

1.  **API Key:** Set `ANYMAILFINDER_API_KEY` environment variable OR be ready to enter key when prompted.
2.  **`domains.txt`:** Create/populate with domains (one per line) in the project root.

## Usage

```bash
python main.py
```

Output: `hr_emails_results_bulk.csv`

## CSV Output Columns

`Domain Searched`, `Category Searched`, `Found Name`, `Found Email`, `Email Verified`, `Job Title`, `LinkedIn URL`, `Search Success`, `API Error Type`, `API Error Explanation`

## API Cost Note

Anymailfinder charges per *verified* email found (2 credits). Unverified/no-finds are free. Duplicate searches within 30 days are free. Use responsibly.
