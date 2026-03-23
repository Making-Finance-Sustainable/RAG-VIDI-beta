## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## Intercoder reliability (binary dummy topics) with bootstrap CIs
## March 2026

##########################################################################
## 1. Dependencies
##########################################################################

import os
import numpy as np
import pandas as pd

## Progress bar
try:
    from tqdm import tqdm
    _HAS_TQDM = True
except Exception:
    _HAS_TQDM = False

np.random.seed(42)

##########################################################################
## 2. Paths
##########################################################################

csv_original = "data/raw/reports_topics.csv"
csv_validation = "data/tidy/reports_topics_validation.csv"
csv_robustness = "data/tidy/reports_topics_robustness.csv"

OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)
out_txt = os.path.join(OUT_DIR, "inter_coder_reliability_bootstrap.txt")

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
    Defaults unknown/missing to False (consistent with your earlier pipeline).
    """
    u = s.astype(str).str.upper().str.strip()
    mapped = u.map({
        "TRUE": True, "FALSE": False,
        "1": True, "0": False,
        "YES": True, "NO": False
    })
    mapped = mapped.fillna(pd.to_numeric(s, errors="coerce").map({1: True, 0: False}))
    return mapped.fillna(False).astype(bool)

def clean_and_subset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"annual_report", "validation"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")

    topic_cols = infer_topic_cols(df)

    df["validation"] = pd.to_numeric(df["validation"], errors="coerce").fillna(0).astype(int)
    df = df.loc[df["validation"] == 1].copy()

    df["annual_report"] = df["annual_report"].astype(str).str.strip()

    for c in topic_cols:
        df[c] = coerce_bool_series(df[c])

    return df

def percent_agreement(y1: np.ndarray, y2: np.ndarray) -> float:
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)
    if y1.size == 0:
        return np.nan
    return float((y1 == y2).mean())

def manual_cohen_kappa(y1: np.ndarray, y2: np.ndarray) -> float:
    """
    Cohen's kappa for binary labels without sklearn.
    Returns np.nan when undefined (e.g., both coders constant => Pe=1).
    """
    y1 = np.asarray(y1, dtype=int)
    y2 = np.asarray(y2, dtype=int)
    if y1.shape != y2.shape:
        raise ValueError("y1 and y2 must have the same shape.")
    n = y1.size
    if n == 0:
        return np.nan

    p0 = (y1 == y2).mean()
    p_yes_1 = y1.mean()
    p_yes_2 = y2.mean()
    p_no_1 = 1 - p_yes_1
    p_no_2 = 1 - p_yes_2
    pe = p_yes_1 * p_yes_2 + p_no_1 * p_no_2

    if np.isclose(1 - pe, 0):
        return np.nan
    return float((p0 - pe) / (1 - pe))

def kappa_score(y1: np.ndarray, y2: np.ndarray) -> float:
    ## Manual version to avoid sklearn RuntimeWarning in degenerate bootstrap draws
    return manual_cohen_kappa(y1, y2)

def krippendorff_alpha_nominal(data: np.ndarray) -> float:
    """
    Krippendorff's alpha for nominal data.
    data: array (n_items, n_coders) with values in {0,1} or np.nan.
    """
    X = np.asarray(data, dtype=float)
    if X.ndim != 2:
        raise ValueError("data must be 2D array (n_items, n_coders)")

    vals = X[~np.isnan(X)]
    if vals.size == 0:
        return np.nan
    cats = np.unique(vals).astype(int)
    cat_to_idx = {c: i for i, c in enumerate(cats)}
    m = len(cats)

    O = np.zeros((m, m), dtype=float)

    for i in range(X.shape[0]):
        row = X[i, :]
        row = row[~np.isnan(row)]
        if row.size < 2:
            continue

        counts = {}
        for v in row.astype(int):
            counts[v] = counts.get(v, 0) + 1

        mi = int(row.size)
        denom = mi - 1
        for c, n_c in counts.items():
            ic = cat_to_idx[c]
            for k, n_k in counts.items():
                ik = cat_to_idx[k]
                O[ic, ik] += (n_c * n_k) / denom

    total = O.sum()
    if total <= 0:
        return np.nan

    diag = np.trace(O)
    Do = (total - diag) / total

    marg = O.sum(axis=1)
    N = marg.sum()
    if N <= 1:
        return np.nan

    exp_agree = float(np.sum(marg * (marg - 1)) / (N * (N - 1)))
    De = 1 - exp_agree

    if np.isclose(De, 0):
        return np.nan

    return float(1 - Do / De)

def safe_nanpercentile(x: np.ndarray, q: float) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return np.nan
    return float(np.percentile(x, q))

def bootstrap_ci_pair(
    y1: np.ndarray,
    y2: np.ndarray,
    stat_fn,
    n_boot: int = 5000,
    alpha: float = 0.05,
) -> tuple:
    """
    Bootstrap percentile CI by resampling documents with replacement (pairwise statistics).
    """
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)
    n = y1.shape[0]
    if n == 0:
        return (np.nan, np.nan, np.nan)

    stats = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = np.random.randint(0, n, size=n)
        stats[b] = stat_fn(y1[idx], y2[idx])

    point = stat_fn(y1, y2)
    lo = safe_nanpercentile(stats, 100 * (alpha / 2))
    hi = safe_nanpercentile(stats, 100 * (1 - alpha / 2))
    return (float(point), float(lo), float(hi))

def bootstrap_ci_items(
    X: np.ndarray,
    stat_fn,
    n_boot: int = 5000,
    alpha: float = 0.05,
) -> tuple:
    """
    Bootstrap percentile CI by resampling items/documents with replacement (matrix statistics).
    X: (n_items, n_coders)
    """
    X = np.asarray(X)
    n = X.shape[0]
    if n == 0:
        return (np.nan, np.nan, np.nan)

    stats = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = np.random.randint(0, n, size=n)
        stats[b] = stat_fn(X[idx, :])

    point = stat_fn(X)
    lo = safe_nanpercentile(stats, 100 * (alpha / 2))
    hi = safe_nanpercentile(stats, 100 * (1 - alpha / 2))
    return (float(point), float(lo), float(hi))

def ensure_alignment_pair(df_a: pd.DataFrame, df_b: pd.DataFrame, topic_cols: list) -> pd.DataFrame:
    return df_a[["annual_report"] + topic_cols].merge(
        df_b[["annual_report"] + topic_cols],
        on="annual_report",
        how="inner",
        suffixes=("_a", "_b"),
    )

def fmt_ci(point, lo, hi, nd=3) -> str:
    if any(pd.isna([point, lo, hi])):
        return "NA"
    return f"{point:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"

def run_pairwise(
    name_a: str,
    name_b: str,
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    topic_cols: list,
    n_boot: int,
    progress_outer_desc: str = "",
) -> dict:
    """
    Per-topic: agreement, kappa, alpha (+ bootstrapped CIs).
    Also computes "overall" flattened metrics across topics.
    """
    aligned = ensure_alignment_pair(df_a, df_b, topic_cols)
    n_common = len(aligned)
    if n_common != 84:
        raise ValueError(
            f"Expected 84 overlapping validation==1 cases between {name_a} and {name_b}, found {n_common}. "
            "Check annual_report IDs match across files."
        )

    topic_iter = topic_cols
    if _HAS_TQDM:
        topic_iter = tqdm(topic_cols, desc=progress_outer_desc, leave=True)

    rows = []
    for t in topic_iter:
        y1 = aligned[f"{t}_a"].astype(int).to_numpy()
        y2 = aligned[f"{t}_b"].astype(int).to_numpy()

        agr, agr_lo, agr_hi = bootstrap_ci_pair(y1, y2, stat_fn=percent_agreement, n_boot=n_boot)
        kap, kap_lo, kap_hi = bootstrap_ci_pair(y1, y2, stat_fn=kappa_score, n_boot=n_boot)

        X = np.column_stack([y1, y2]).astype(float)
        alp, alp_lo, alp_hi = bootstrap_ci_items(X, stat_fn=krippendorff_alpha_nominal, n_boot=n_boot)

        rows.append({
            "topic": t,
            "n_docs": n_common,
            "agreement": agr,
            "agreement_ci_low": agr_lo,
            "agreement_ci_high": agr_hi,
            "kappa": kap,
            "kappa_ci_low": kap_lo,
            "kappa_ci_high": kap_hi,
            "alpha": alp,
            "alpha_ci_low": alp_lo,
            "alpha_ci_high": alp_hi,
            "prevalence_a": float(y1.mean()),
            "prevalence_b": float(y2.mean()),
        })

    per_topic = pd.DataFrame(rows).sort_values("alpha", ascending=False)

    ## Overall (flatten across topics)
    A = aligned[[f"{t}_a" for t in topic_cols]].astype(int).to_numpy().reshape(-1)
    B = aligned[[f"{t}_b" for t in topic_cols]].astype(int).to_numpy().reshape(-1)

    overall_ag, overall_ag_lo, overall_ag_hi = bootstrap_ci_pair(A, B, stat_fn=percent_agreement, n_boot=n_boot)
    overall_k, overall_k_lo, overall_k_hi = bootstrap_ci_pair(A, B, stat_fn=kappa_score, n_boot=n_boot)

    Xflat = np.column_stack([A, B]).astype(float)
    overall_alp, overall_alp_lo, overall_alp_hi = bootstrap_ci_items(Xflat, stat_fn=krippendorff_alpha_nominal, n_boot=n_boot)

    summary = {
        "comparison": f"{name_a} vs {name_b}",
        "n_docs": n_common,
        "n_topics": len(topic_cols),
        "overall_agreement": overall_ag,
        "overall_agreement_ci_low": overall_ag_lo,
        "overall_agreement_ci_high": overall_ag_hi,
        "overall_kappa": overall_k,
        "overall_kappa_ci_low": overall_k_lo,
        "overall_kappa_ci_high": overall_k_hi,
        "overall_alpha": overall_alp,
        "overall_alpha_ci_low": overall_alp_lo,
        "overall_alpha_ci_high": overall_alp_hi,
        "macro_agreement_mean": float(per_topic["agreement"].mean()),
        "macro_agreement_median": float(per_topic["agreement"].median()),
        "macro_kappa_mean": float(per_topic["kappa"].mean()),
        "macro_kappa_median": float(per_topic["kappa"].median()),
        "macro_alpha_mean": float(per_topic["alpha"].mean()),
        "macro_alpha_median": float(per_topic["alpha"].median()),
    }

    return {"summary": summary, "per_topic": per_topic}

##########################################################################
## 4. Load datasets and validate
##########################################################################

df_orig = clean_and_subset(csv_original)
df_val = clean_and_subset(csv_validation)
df_rob = clean_and_subset(csv_robustness)

topic_cols = infer_topic_cols(df_orig)

missing_in_val = [c for c in topic_cols if c not in df_val.columns]
missing_in_rob = [c for c in topic_cols if c not in df_rob.columns]
if missing_in_val or missing_in_rob:
    raise ValueError(
        "Topic columns mismatch:\n"
        f"Missing in validation: {missing_in_val}\n"
        f"Missing in robustness: {missing_in_rob}"
    )

for label, d in [("original", df_orig), ("validation", df_val), ("robustness", df_rob)]:
    if len(d) != 84:
        raise ValueError(f"Expected 84 rows with validation==1 in {label}, found {len(d)}.")

##########################################################################
## 5. Compute reliability (pairwise only)
##########################################################################

N_BOOT = 5000

if not _HAS_TQDM:
    print("Note: tqdm is not installed; install with: pip install tqdm")

res_ov = run_pairwise(
    name_a="original",
    name_b="validation",
    df_a=df_orig,
    df_b=df_val,
    topic_cols=topic_cols,
    n_boot=N_BOOT,
    progress_outer_desc="original vs validation (per-topic bootstrap)",
)

res_vr = run_pairwise(
    name_a="validation",
    name_b="robustness",
    df_a=df_val,
    df_b=df_rob,
    topic_cols=topic_cols,
    n_boot=N_BOOT,
    progress_outer_desc="validation vs robustness (per-topic bootstrap)",
)

##########################################################################
## 6. Write TXT report
##########################################################################

def write_block(f, result: dict) -> None:
    s = result["summary"]
    pt = result["per_topic"].copy()  # already sorted by alpha desc

    f.write(f"\n=== {s['comparison']} ===\n")
    f.write(f"Documents (validation==1, matched): {s['n_docs']}\n")
    f.write(f"Topics: {s['n_topics']}\n")
    f.write(f"Bootstrap: {N_BOOT} item-resamples, percentile 95% CIs\n\n")

    f.write(f"Overall percent agreement (flattened): {fmt_ci(s['overall_agreement'], s['overall_agreement_ci_low'], s['overall_agreement_ci_high'])}\n")
    f.write(f"Overall Cohen's kappa (flattened): {fmt_ci(s['overall_kappa'], s['overall_kappa_ci_low'], s['overall_kappa_ci_high'])}\n")
    f.write(f"Overall Krippendorff's alpha (flattened): {fmt_ci(s['overall_alpha'], s['overall_alpha_ci_low'], s['overall_alpha_ci_high'])}\n")

    f.write(f"Macro agreement mean/median: {s['macro_agreement_mean']:.3f} / {s['macro_agreement_median']:.3f}\n")
    f.write(f"Macro kappa mean/median: {s['macro_kappa_mean']:.3f} / {s['macro_kappa_median']:.3f}\n")
    f.write(f"Macro alpha mean/median: {s['macro_alpha_mean']:.3f} / {s['macro_alpha_median']:.3f}\n")

    f.write("\nTopics ordered by Krippendorff's alpha:\n")
    for _, row in pt.iterrows():
        f.write(
            f"  {row['topic']}: "
            f"alpha={fmt_ci(row['alpha'], row['alpha_ci_low'], row['alpha_ci_high'])}, "
            f"kappa={fmt_ci(row['kappa'], row['kappa_ci_low'], row['kappa_ci_high'])}, "
            f"agreement={fmt_ci(row['agreement'], row['agreement_ci_low'], row['agreement_ci_high'])}, "
            f"prev_a={row['prevalence_a']:.3f}, prev_b={row['prevalence_b']:.3f}\n"
        )

with open(out_txt, "w", encoding="utf-8") as f:
    f.write("Making Finance Sustainable VIDI Project\n")
    f.write("Intercoder reliability on validation subset (validation==1)\n")
    f.write("Labels are binary dummies per topic (_present columns).\n")
    f.write("Per-topic statistics + bootstrapped 95% CIs.\n\n")
    f.write(f"Original:   {csv_original}\n")
    f.write(f"Validation: {csv_validation}\n")
    f.write(f"Robustness: {csv_robustness}\n")

    write_block(f, res_ov)
    write_block(f, res_vr)

print("Done.")
print(f"TXT report saved: {out_txt}")