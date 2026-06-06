# ContextLink Workflow
ContextLink combines automated entity matching, alter-alter tie transfer, and future human review.

## 1. Input
The input is survey-style social network data containing:
- Respondent ID
- Close tie names
- Local tie names
- Filter columns indicating which local ties need to be matched
- Close-network alter-alter relationship columns
Example relationship columns:
- `cn1_cn2_interact_no_u`
- `cn1_cn3_interact_no_u`
- `cn2_cn4_interact_no_u`
These columns represent whether two close-network alters know or interact with each other.

## 2. Stage 1: Entity Matching
The pipeline compares local tie names against close tie names within the same respondent row.
Matching logic includes:
- Removing punctuation and whitespace.
- Exact matching for short names and initials.
- Normalized matching for longer names.
- Ambiguity detection when multiple matches exist.
- Recording unmatched cases for later review.
The output identifies mappings such as:
`local_name1` → `close_name2`

## 3. Stage 2: Alter-Alter Tie Transfer
After entity mappings are created, the pipeline uses them to transfer relationship values.
Example:
If:
- `local_name1` maps to `close_name2`
- `local_name3` maps to `close_name4`
Then:
`cn2_cn4_interact_no_u` can be copied to `ln1_ln3_interact_no_u`.
This turns entity matching into network data completion.

## 4. Human Review
The Streamlit app is being developed to help researchers review:
- Ambiguous name matches
- Unmatched cases
- Tie transfer decisions
- Reviewer notes and corrections

## 5. Export
The final reviewed output can be exported for cleaned research data analysis.
