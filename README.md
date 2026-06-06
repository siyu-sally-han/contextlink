# ContextLink
ContextLink is a human-in-the-loop data cleaning tool for social network survey data. It combines entity matching with alter-alter tie transfer to help researchers validate and complete messy network survey records.
This project started from a real research data-cleaning problem: the same person may appear across multiple survey sections with inconsistent names, initials, nicknames, punctuation, or role-based labels. Once the same person is identified across sections, their relationship information can be transferred to complete missing local-network tie data.

## What ContextLink Does
The current pipeline has two stages:
1. **Entity Matching**  
   Match local tie names to close tie names using conservative rule-based matching.
2. **Alter-Alter Tie Transfer**  
   Use matched entity indices to copy alter-alter relationship values from close-network columns to local-network columns.

## Why This Matters
Social network survey data often contains messy human-entered names and repeated people across multiple network sections. Fully manual cleaning is slow, while fully automated matching can be risky for ambiguous names, initials, and role labels.
ContextLink explores a hybrid workflow:
- Automatically identify likely matches.
- Track unmatched or ambiguous cases.
- Transfer relationship values when entity mappings are reliable.
- Prepare uncertain cases for future human review.

## Example
If the pipeline finds that:
- `local_name1` refers to `close_name2`
- `local_name3` refers to `close_name4`
Then it can transfer:
`cn2_cn4_interact_no_u` → `ln1_ln3_interact_no_u`
In plain language: if two people are known to be the same individuals across survey sections, their existing relationship information can be reused to complete the local-network data.

## Repository Structure
```text
contextlink/
  pipeline/
    matching_pipeline.R
    sample_survey_data.csv
    README.md
  app/
    README.md
    requirements.txt
  docs/
    workflow.md
    data_privacy.md
