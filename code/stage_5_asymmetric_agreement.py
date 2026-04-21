## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## Asymmetric agreement for binary topic columns (_present)
## TXT output only
## No validation filter
## March 2026

##########################################################################
## 1. Dependencies
##########################################################################

import os
import numpy as np
import pandas as pd

##########################################################################
## 2. Paths
##########################################################################

csv_file1 = "data/tidy/reports_topics_memberships.csv"
csv_file2 = "data/tidy/reports_topics_validation.csv"

OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)
out_txt = os.path.join(OUT_DIR, "asymmetric_agreement.txt")

##########################################################################
## 3. Helpers
##########################################################################

def infer_topic_cols(df: pd.DataFrame) -> list:
    cols = [c for c in df.columns if c.endswith("_present")]
    if not cols:
        raise ValueError("No topic columns found. Expected columns ending with '_present'.")
    return cols

def coerce_bool_series(s: pd.Series) -> pd.Series:
    """
    Convert to boolean robustly.
    Accepts True/False, 1/0, YES/NO, and strings.
    Defaults unknown/missing to False.
    This version avoids the pandas FutureWarning related to fillna downcasting.
    """
    s_str = s.astype(str).str.upper().str.strip()

    text_map = {
        "TRUE": True,
        "FALSE": False,
        "1": True,
        "0": False,
        "YES": True,
        "NO": False
    }

    out = s_str.map(text_map)
    numeric = pd.to_numeric(s, errors="coerce")
    out = out.where(~out.isna(), numeric.map({1: True, 0: False}))

    return out.eq(True)

def clean_file(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"company"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")

    topic_cols = infer_topic_cols(df)

    df["company"] = df["company"].astype(str).str.strip()

    for c in topic_cols:
        df[c] = coerce_bool_series(df[c])

    return df

def ensure_alignment_pair(df_a: pd.DataFrame, df_b: pd.DataFrame, topic_cols: list) -> pd.DataFrame:
    aligned = df_a[["company"] + topic_cols].merge(
        df_b[["company"] + topic_cols],
        on="company",
        how="inner",
        suffixes=("_a", "_b"),
    )

    if aligned.empty:
        raise ValueError(
            "No overlapping company values found between the two files."
        )

    return aligned

def asymmetric_agreement(y1: np.ndarray, y2: np.ndarray) -> dict:
    """
    Agreement from file 1 to file 2:
    among cases where y1 is TRUE, how many are also TRUE in y2?
    """
    y1 = np.asarray(y1, dtype=bool)
    y2 = np.asarray(y2, dtype=bool)

    true_in_a = int(y1.sum())
    true_in_b = int(y2.sum())
    true_in_both = int((y1 & y2).sum())

    if true_in_a == 0:
        agreement = np.nan
    else:
        agreement = true_in_both / true_in_a

    return {
        "n_true_file1": true_in_a,
        "n_true_file2": true_in_b,
        "n_true_both": true_in_both,
        "agreement_file1_to_file2": agreement
    }

def run_pairwise_asymmetric(
    name_a: str,
    name_b: str,
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    topic_cols: list,
) -> dict:
    aligned = ensure_alignment_pair(df_a, df_b, topic_cols)
    n_common = len(aligned)

    rows = []
    for t in topic_cols:
        y1 = aligned[f"{t}_a"].to_numpy()
        y2 = aligned[f"{t}_b"].to_numpy()

        res = asymmetric_agreement(y1, y2)

        rows.append({
            "topic": t,
            "n_docs_matched": n_common,
            "n_true_file1": res["n_true_file1"],
            "n_true_file2": res["n_true_file2"],
            "n_true_both": res["n_true_both"],
            "agreement_file1_to_file2": res["agreement_file1_to_file2"]
        })

    per_topic = pd.DataFrame(rows).sort_values(
        by="agreement_file1_to_file2",
        ascending=False,
        na_position="last"
    )

    ## Overall pooled measure across all topic-columns
    A = aligned[[f"{t}_a" for t in topic_cols]].to_numpy().astype(bool).reshape(-1)
    B = aligned[[f"{t}_b" for t in topic_cols]].to_numpy().astype(bool).reshape(-1)

    overall = asymmetric_agreement(A, B)

    summary = {
        "comparison": f"{name_a} -> {name_b}",
        "n_docs_matched": n_common,
        "n_topics": len(topic_cols),
        "overall_n_true_file1": overall["n_true_file1"],
        "overall_n_true_file2": overall["n_true_file2"],
        "overall_n_true_both": overall["n_true_both"],
        "overall_agreement_file1_to_file2": overall["agreement_file1_to_file2"],
        "macro_mean_agreement": float(per_topic["agreement_file1_to_file2"].mean(skipna=True)),
        "macro_median_agreement": float(per_topic["agreement_file1_to_file2"].median(skipna=True)),
    }

    return {"summary": summary, "per_topic": per_topic}

def fmt_num(x, nd=3) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.{nd}f}"

##########################################################################
## 4. Load datasets and validate
##########################################################################

df1 = clean_file(csv_file1)
df2 = clean_file(csv_file2)

topic_cols_1 = infer_topic_cols(df1)
topic_cols_2 = infer_topic_cols(df2)

missing_in_2 = [c for c in topic_cols_1 if c not in topic_cols_2]
missing_in_1 = [c for c in topic_cols_2 if c not in topic_cols_1]

if missing_in_2 or missing_in_1:
    raise ValueError(
        "Topic columns mismatch:\n"
        f"Missing in file2: {missing_in_2}\n"
        f"Missing in file1: {missing_in_1}"
    )

topic_cols = topic_cols_1

##########################################################################
## 5. Compute asymmetric agreement
##########################################################################

res = run_pairwise_asymmetric(
    name_a="file1",
    name_b="file2",
    df_a=df1,
    df_b=df2,
    topic_cols=topic_cols,
)

##########################################################################
## 6. Write TXT report only
##########################################################################

with open(out_txt, "w", encoding="utf-8") as f:
    s = res["summary"]
    pt = res["per_topic"]

    f.write("Making Finance Sustainable VIDI Project\n")
    f.write("Asymmetric agreement for binary topic columns (_present)\n")
    f.write("TXT output only\n")
    f.write("No validation filter applied\n")
    f.write("Agreement is calculated as:\n")
    f.write("TRUE in file 1 AND TRUE in file 2 / TRUE in file 1\n\n")

    f.write(f"File 1: {csv_file1}\n")
    f.write(f"File 2: {csv_file2}\n\n")

    f.write(f"Comparison: {s['comparison']}\n")
    f.write(f"Matched documents: {s['n_docs_matched']}\n")
    f.write(f"Topics: {s['n_topics']}\n\n")

    f.write("Overall pooled results across all topic-columns:\n")
    f.write(f"  TRUE in file 1: {s['overall_n_true_file1']}\n")
    f.write(f"  TRUE in file 2: {s['overall_n_true_file2']}\n")
    f.write(f"  TRUE in both:   {s['overall_n_true_both']}\n")
    f.write(f"  Agreement file1 -> file2: {fmt_num(s['overall_agreement_file1_to_file2'])}\n")
    f.write(f"  Macro mean agreement:     {fmt_num(s['macro_mean_agreement'])}\n")
    f.write(f"  Macro median agreement:   {fmt_num(s['macro_median_agreement'])}\n\n")

    f.write("Per-topic results:\n")
    for _, row in pt.iterrows():
        f.write(
            f"  {row['topic']}: "
            f"TRUE_file1={int(row['n_true_file1'])}, "
            f"TRUE_file2={int(row['n_true_file2'])}, "
            f"TRUE_both={int(row['n_true_both'])}, "
            f"agreement={fmt_num(row['agreement_file1_to_file2'])}\n"
        )

print("Done.")
print(f"TXT report saved: {out_txt}")