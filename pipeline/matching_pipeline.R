# ContextLink: Entity Matching + Alter-Alter Tie Transfer Pipeline
# This script demonstrates a two-stage pipeline for social network survey data:
#   Stage 1: Match local tie names to close tie names.
#   Stage 2: Transfer alter-alter relationship values based on matched indices.
#
# This public version uses synthetic sample data only.

library(dplyr)
library(tidyr)
library(stringr)
library(purrr)
library(tibble)

# -----------------------------
# 0. Paths
# -----------------------------

input_path <- "pipeline/sample_survey_data.csv"
output_dir <- "pipeline/sample_outputs"

if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# -----------------------------
# 1. Load sample data
# -----------------------------

df <- read.csv(
  input_path,
  header = TRUE,
  stringsAsFactors = FALSE
)

names(df) <- trimws(names(df))

# -----------------------------
# 2. Helper functions
# -----------------------------

normalize_name <- function(x) {
  x <- ifelse(is.na(x), "", x)
  x <- gsub("[[:punct:][:space:]]+", "", x)
  tolower(x)
}

get_close_name_cols <- function(df) {
  grep("^close_name\\d+$", names(df), value = TRUE)
}

get_local_name_col <- function(j) {
  paste0("local_name", j)
}

get_filter_col <- function(j) {
  paste0("name", j, "_filter")
}

extract_col_number <- function(col_name) {
  as.integer(str_extract(col_name, "\\d+"))
}

make_close_tie_col <- function(c1, c2) {
  paste0("cn", min(c1, c2), "_cn", max(c1, c2), "_interact_no_u")
}

make_local_tie_col <- function(n1, n2) {
  paste0("ln", min(n1, n2), "_ln", max(n1, n2), "_interact_no_u")
}

# -----------------------------
# 3. Stage 1: Entity matching
# -----------------------------

match_group <- function(df, j) {
  local_col <- get_local_name_col(j)
  filter_col <- get_filter_col(j)
  close_name_cols <- get_close_name_cols(df)

  if (!local_col %in% names(df)) {
    stop(paste("Missing local name column:", local_col))
  }

  if (!filter_col %in% names(df)) {
    stop(paste("Missing filter column:", filter_col))
  }

  yes_rows <- which(tolower(df[[filter_col]]) == "yes")

  res <- tibble(
    orig_row = yes_rows,
    local_slot = j,
    local_name = df[[local_col]][yes_rows],
    matched_name = NA_character_,
    matched_col = NA_character_,
    match_status = "unmatched",
    reason = NA_character_
  )

  for (k in seq_along(yes_rows)) {
    i <- yes_rows[k]
    local_nm <- df[[local_col]][i]
    close_names <- as.character(df[i, close_name_cols])

    normalized_local <- normalize_name(local_nm)
    normalized_close <- normalize_name(close_names)

    idxs <- integer(0)
    reason <- NA_character_

    if (is.na(local_nm) || local_nm == "" || normalized_local == "") {
      reason <- "missing local name"

    } else if (nchar(normalized_local) <= 2) {
      # Short entries such as initials are high-risk, so require exact match.
      idxs <- which(tolower(local_nm) == tolower(close_names))

      if (length(idxs) == 0) {
        reason <- "short name: no exact match"
      }

    } else {
      # For longer names, allow punctuation/space-insensitive matching.
      stripped_idxs <- which(normalized_close == normalized_local)

      if (length(stripped_idxs) == 0) {
        reason <- "no normalized match"
      } else {
        idxs <- stripped_idxs

        # If multiple normalized matches exist, prefer exact match.
        if (length(idxs) > 1) {
          exact_idxs <- which(tolower(close_names[idxs]) == tolower(local_nm))

          if (length(exact_idxs) > 0) {
            idxs <- idxs[exact_idxs]
          } else {
            reason <- "multiple normalized matches, no exact match"
          }
        }
      }
    }

    if (length(idxs) == 1) {
      res$matched_name[k] <- close_names[idxs]
      res$matched_col[k] <- close_name_cols[idxs]
      res$match_status[k] <- "matched"
    } else if (length(idxs) > 1) {
      res$match_status[k] <- "ambiguous"
      res$reason[k] <- "multiple possible matches"
    }

    if (!is.na(reason)) {
      res$reason[k] <- reason
    }
  }

  return(res)
}

entity_matches <- bind_rows(
  lapply(1:7, function(j) match_group(df, j))
)

matched_entities <- entity_matches %>%
  filter(match_status == "matched") %>%
  mutate(
    close_slot = extract_col_number(matched_col)
  )

# Save entity matching outputs
write.csv(
  entity_matches,
  file.path(output_dir, "entity_matches_all.csv"),
  row.names = FALSE
)

write.csv(
  matched_entities,
  file.path(output_dir, "entity_matches_successful.csv"),
  row.names = FALSE
)

# -----------------------------
# 4. Stage 2: Build alter-alter tie transfer jobs
# -----------------------------

copy_jobs <- matched_entities %>%
  group_by(orig_row) %>%
  filter(n() >= 2) %>%
  summarise(
    local_slots = list(local_slot),
    close_slots = list(close_slot),
    matched_names = list(matched_name),
    copy_jobs = list({
      pairs <- combn(seq_along(local_slots[[1]]), 2, simplify = FALSE)

      map_dfr(pairs, function(pair) {
        local_1 <- local_slots[[1]][pair[1]]
        local_2 <- local_slots[[1]][pair[2]]

        close_1 <- close_slots[[1]][pair[1]]
        close_2 <- close_slots[[1]][pair[2]]

        name_1 <- matched_names[[1]][pair[1]]
        name_2 <- matched_names[[1]][pair[2]]

        # Skip invalid self-pairs.
        if (local_1 == local_2 || close_1 == close_2) {
          return(NULL)
        }

        tibble(
          orig_row = orig_row,
          local_pair = paste0("local_name", local_1, " & local_name", local_2),
          close_pair = paste0("close_name", close_1, " & close_name", close_2),
          matched_pair = paste(name_1, "&", name_2),
          source_col = make_close_tie_col(close_1, close_2),
          target_col = make_local_tie_col(local_1, local_2)
        )
      })
    }),
    .groups = "drop"
  ) %>%
  select(orig_row, copy_jobs) %>%
  unnest(copy_jobs)

# -----------------------------
# 5. Stage 2: Transfer tie values
# -----------------------------

df_filled <- df

copy_jobs$source_exists <- FALSE
copy_jobs$copied_value <- NA_character_
copy_jobs$copy_status <- "not copied"

for (i in seq_len(nrow(copy_jobs))) {
  row_id <- copy_jobs$orig_row[i]
  source_col <- copy_jobs$source_col[i]
  target_col <- copy_jobs$target_col[i]

  if (!target_col %in% names(df_filled)) {
    df_filled[[target_col]] <- NA
  }

  if (source_col %in% names(df_filled)) {
    df_filled[[target_col]][row_id] <- df_filled[[source_col]][row_id]

    copy_jobs$source_exists[i] <- TRUE
    copy_jobs$copied_value[i] <- as.character(df_filled[[source_col]][row_id])
    copy_jobs$copy_status[i] <- "copied"
  } else {
    copy_jobs$copy_status[i] <- "source column not found"
  }
}

# -----------------------------
# 6. Export outputs
# -----------------------------

write.csv(
  copy_jobs,
  file.path(output_dir, "alter_tie_transfer_jobs.csv"),
  row.names = FALSE
)

write.csv(
  df_filled,
  file.path(output_dir, "filled_survey_data.csv"),
  row.names = FALSE
)

cat("ContextLink pipeline completed.\n")
cat("Total entity match attempts:", nrow(entity_matches), "\n")
cat("Successful entity matches:", nrow(matched_entities), "\n")
cat("Alter-alter tie transfer jobs:", nrow(copy_jobs), "\n")
cat("Successfully copied tie values:", sum(copy_jobs$copy_status == "copied"), "\n")
