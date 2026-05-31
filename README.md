# contextlink
Human-in-the-loop entity matching tool for social network survey data.

# ContextLink
ContextLink is a human-in-the-loop entity matching tool for social network survey data. It combines a rule-based matching pipeline with an interactive review interface to help researchers identify, validate, and export ambiguous person matches across survey sections. This project started from a real research data-cleaning problem: the same person may appear in different parts of a survey with inconsistent names, initials, nicknames, punctuation, or role-based labels.

## Project Structure
This repository currently includes two parts:
1. `pipeline/` — an R-based matching pipeline that processes survey-style social network data and generates candidate matches.
2. `app/` — a Streamlit prototype that allows human reviewers to inspect and confirm ambiguous matches.

## Why this matters
Social network survey data often contains messy human-entered names. Fully automated matching can miss ambiguous cases, while fully manual cleaning is slow and hard to audit. ContextLink explores a hybrid workflow: automated matching first, human review second.

## Current Features
- Rule-based name cleaning and matching
- Conservative handling of short names and initials
- Candidate match generation
- Pairwise alter combination generation
- Synthetic sample data for public demonstration
- Early Streamlit prototype for human-in-the-loop review

## Tech Stack
- R
- dplyr
- tidyr
- stringr
- purrr
- tibble
- Python
- Streamlit

## Data Privacy
This public repository does not include any real respondent data. All sample data is synthetic and created only to demonstrate the matching logic and review workflow.

## Status
Early technical prototype. The R pipeline is being cleaned into a reproducible module, and the Streamlit app is being developed as a review interface for ambiguous matches.
