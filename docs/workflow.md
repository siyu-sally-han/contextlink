# ContextLink Workflow
ContextLink combines automated matching with human review.

## 1. Input
The input is survey-style social network data containing:
- Respondent ID
- Close tie names
- Local tie names
- Filter columns indicating which local ties need to be matched

## 2. Automated Matching
The R pipeline standardizes names and compares local tie names against close tie names.
Matching logic includes:
- Removing punctuation and whitespace
- Exact matching for short names and initials
- Stripped matching for longer names
- Ambiguity detection when multiple matches exist
- Flagging unmatched cases for review

## 3. Candidate Generation
The pipeline generates candidate matched names and pairwise alter combinations.

## 4. Human Review
The Streamlit app is designed to let researchers review candidate matches, confirm or reject them, and add reviewer notes.

## 5. Export
The final reviewed output can be exported for cleaned research data analysis.
