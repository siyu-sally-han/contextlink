# ContextLink Pipeline
This folder contains the technical pipeline for ContextLink, a human-in-the-loop data cleaning tool for social network survey data.
The pipeline has two stages:
1. **Entity Matching** — match local tie names to close tie names.
2. **Alter-Alter Tie Transfer** — use matched entity indices to copy alter-alter relationship values from close-network columns to local-network columns.

## Stage 1: Entity Matching
The first stage compares `local_name1`–`local_name7` against `close_name1`–`close_name7`.
The matching logic:
- Removes punctuation and whitespace for normalized comparison.
- Uses exact matching for short names and initials.
- Uses normalized matching for longer names.
- Records unmatched or ambiguous cases for review.
- Outputs successful matches and all attempted matches.
Example:
`local_name1 = "Alex"` matches `close_name1 = "Alex"`.

## Stage 2: Alter-Alter Tie Transfer
After local names are matched to close names, the pipeline transfers relationship values.
Example:
If:
- `local_name1` matches `close_name2`
- `local_name3` matches `close_name4`
Then the pipeline maps:
`cn2_cn4_interact_no_u` → `ln1_ln3_interact_no_u`
This means that if the close-network data already knows whether close person 2 and close person 4 know each other, that value can be copied to the corresponding local-network pair.

## Files
- `matching_pipeline.R` — main two-stage pipeline
- `sample_survey_data.csv` — synthetic sample input data
- `sample_outputs/` — generated output files

## Outputs
Running the pipeline generates:
- `entity_matches_all.csv`
- `entity_matches_successful.csv`
- `alter_tie_transfer_jobs.csv`
- `filled_survey_data.csv`

## How to Run
Install required R packages:
`install.packages(c("dplyr", "tidyr", "stringr", "purrr", "tibble"))`
Then run:
`source("pipeline/matching_pipeline.R")`

## Privacy Note

This folder uses synthetic sample data only. No real respondent data, real names, or private survey files are included.
