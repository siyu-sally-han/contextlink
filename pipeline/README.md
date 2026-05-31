# Matching Pipeline
This folder contains the rule-based matching pipeline for ContextLink.
The pipeline processes survey-style social network data and generates candidate matches between local tie names and close tie names.

## What it does
1. Loads synthetic survey data.
2. Cleans names by removing punctuation and whitespace.
3. Matches local tie names against close tie names.
4. Handles short names and initials conservatively.
5. Flags unmatched or ambiguous cases.
6. Creates structured matched-name tables.
7. Generates pairwise combinations for downstream review.

## Files
- `matching_pipeline.R` — main R script
- `sample_survey_data.csv` — synthetic input data
- `sample_outputs/` — sample generated outputs

## How to Run
Install required packages in R:
`install.packages(c("dplyr", "tidyr", "stringr", "purrr", "tibble"))`

Then run:
`source("pipeline/matching_pipeline.R")`

## Privacy Note
This folder uses synthetic sample data only. No real respondent data is included.
