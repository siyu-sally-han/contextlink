# ContextLink: Entity Matching Pipeline
# This script demonstrates a rule-based matching pipeline for social network survey data.
# It uses synthetic sample data only.

library(dplyr)
library(tidyr)
library(stringr)
library(purrr)
library(tibble)

# -----------------------------
# 1. Load sample data
# -----------------------------

df <- read.csv(
  "pipeline/sample_survey_data.csv",
  header = TRUE,
  stringsAsFactors = FALSE
)

names(df) <- trimws(names(df))

# -----------------------------
# 2. Helper functions
# -----------------------------

strip_punct <- function(x) {
  gsub("[[:punct:][:space:]]+", "", x)
}

match_group <- function(df, j) {
  local_col  <- paste0("local_name", j)
  filter_col <- paste0("name", j, "_filter")
  close_name_cols <- grep("^close_name\\d+$", names(df), value = TRUE)

  yes_rows <- which(tolower(df[[filter_col]]) == "yes")

  res <- tibble(
    orig_row = yes_rows,
    local_name = df[[local_col]][yes_rows],
    group_j = j,
    matched_names = NA_character_,
    matched_cols = NA_character_,
    reason = NA_character_
  )

  for (k in seq_along(yes_rows)) {
    i <- yes_rows[k]
    local_nm <- df[[local_col]][i]
    vect <- as.character(df[i, close_name_cols])

    s_local <- tolower(strip_punct(local_nm))
    s_vect <- tolower(strip_punct(vect))

    idxs <- integer(0)
    reason <- NA_character_

    if (is.na(local_nm) || local_nm == "") {
      reason <- "missing local name"
    } else if (nchar(s_local) <= 2) {
      idxs <- which(tolower(local_nm) == tolower(vect))
      if (length(idxs) == 0) {
        reason <- "short name: no exact match"
      }
    } else {
      stripped_idxs <- which(s_vect == s_local)

      if (length(stripped_idxs) == 0) {
        reason <- "no stripped match"
      } else {
        idxs <- stripped_idxs

        if (length(idxs) > 1) {
          exact_idxs <- which(tolower(vect[idxs]) == tolower(local_nm))

          if (length(exact_idxs) > 0) {
            idxs <- idxs[exact_idxs]
          } else {
            reason <- "multiple stripped matches, no exact match"
          }
        }
      }
    }

    if (length(idxs) == 1) {
      res$matched_names[k] <- vect[idxs]
      res$matched_cols[k] <- close_name_cols[idxs]
    }

    res$reason[k] <- reason
  }

  return(res)
}

# -----------------------------
# 3. Run matching across local-name groups
# -----------------------------

out_tbl_all <- bind_rows(
  lapply(1:7, function(j) match_group(df, j))
)

matched_only <- out_tbl_all %>%
  filter(!is.na(matched_names), matched_names != "") %>%
  group_by(orig_row) %>%
  mutate(match_id = row_number()) %>%
  ungroup()

# -----------------------------
# 4. Convert matching results to wide format
# -----------------------------

names_wide <- matched_only %>%
  select(orig_row, group_j, matched_names) %>%
  pivot_wider(
    id_cols = orig_row,
    names_from = group_j,
    values_from = matched_names,
    names_prefix = "matched_name_"
  )

cols_wide <- matched_only %>%
  select(orig_row, group_j, matched_cols) %>%
  pivot_wider(
    id_cols = orig_row,
    names_from = group_j,
    values_from = matched_cols,
    names_prefix = "matched_col_"
  )

final_matched_tbl <- left_join(names_wide, cols_wide, by = "orig_row")

filtered_tbl <- final_matched_tbl %>%
  rowwise() %>%
  mutate(
    matched_name_count = sum(!is.na(c_across(starts_with("matched_name_"))))
  ) %>%
  ungroup() %>%
  filter(matched_name_count >= 2) %>%
  select(-matched_name_count)

# -----------------------------
# 5. Generate pairwise combinations
# -----------------------------

combo_tbl <- filtered_tbl %>%
  rowwise() %>%
  mutate(
    combos = list({
      v <- na.omit(c_across(starts_with("matched_name_")))

      if (length(v) > 1) {
        combn(
          v,
          2,
          FUN = function(x) paste(x, collapse = " & "),
          simplify = TRUE
        )
      } else {
        character(0)
      }
    })
  ) %>%
  ungroup() %>%
  select(orig_row, combos) %>%
  unnest(cols = combos)

# -----------------------------
# 6. Export outputs
# -----------------------------

if (!dir.exists("pipeline/sample_outputs")) {
  dir.create("pipeline/sample_outputs", recursive = TRUE)
}

write.csv(
  filtered_tbl,
  "pipeline/sample_outputs/sample_matched_pairs.csv",
  row.names = FALSE
)

write.csv(
  combo_tbl,
  "pipeline/sample_outputs/sample_pairwise_combinations.csv",
  row.names = FALSE
)

cat("ContextLink matching pipeline completed.\n")
cat("Rows with at least two matched names:", nrow(filtered_tbl), "\n")
cat("Pairwise combinations generated:", nrow(combo_tbl), "\n")
