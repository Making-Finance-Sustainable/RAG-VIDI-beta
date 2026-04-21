## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## Intercoder reliability (binary dummy topics) with bootstrap CIs
## March 2026

import re
import unicodedata
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------
# Configuration
# ----------------------------
FILE1 = "data/tidy/reports_topics_validation.csv"
FILE2 = "data/raw/memberships.csv"
FILE3 = "data/raw/organisation_categories.csv"

OUT_MATCHED = "results/memberships.csv"
OUT_COMPANY_TOPICS = "data/tidy/reports_topics_memberships.csv"

COMPANY_COL_1 = "company"
COMPANY_COL_2 = "Company"
INIT_COL = "Initiative"
TYPE_COL = "Type"

SIM_THRESHOLD = 0.90
MAX_MEMBERSHIPS = None

TOPIC_COLS = [
    "sustainable_development_present",
    "responsible_investment_esg_present",
    "green_growth_present",
    "net_zero_present",
    "decarbonization_present",
    "transition_finance_present",
    "conservation_finance_present",
]

VECTORIZER_KWARGS = dict(
    analyzer="char_wb",
    ngram_range=(3, 5),
    min_df=1
)

# ----------------------------
# Helpers
# ----------------------------
def normalize_company_name(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()

    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    s = re.sub(r"[^a-z0-9\s]", " ", s)

    suffixes = [
        "inc", "incorporated", "corp", "corporation", "co", "company",
        "ltd", "limited", "plc", "ag", "sa", "spa", "nv", "bv",
        "gmbh", "kg", "llc", "lp", "sarl", "oyj", "ab", "as"
    ]
    tokens = [t for t in s.split() if t not in suffixes]
    s = " ".join(tokens)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def safe_col(df: pd.DataFrame, col: str):
    if col not in df.columns:
        raise ValueError(f"Missing expected column '{col}'. Available: {list(df.columns)}")

def to_bool(x):
    if pd.isna(x):
        return False
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    return s in ("true", "t", "1", "yes", "y")

# ----------------------------
# Main
# ----------------------------
def main():
    df1 = pd.read_csv(FILE1, encoding="utf-8")
    df2 = pd.read_csv(FILE2, encoding="utf-8")
    df3 = pd.read_csv(FILE3, encoding="utf-8")

    safe_col(df1, COMPANY_COL_1)
    safe_col(df2, COMPANY_COL_2)
    safe_col(df2, INIT_COL)
    safe_col(df2, TYPE_COL)

    safe_col(df3, INIT_COL)
    for c in TOPIC_COLS:
        safe_col(df3, c)

    # Preserve original order
    df1 = df1.copy()
    df1["_row_id"] = np.arange(len(df1))

    # Normalise names for matching
    df1["_company_norm"] = df1[COMPANY_COL_1].map(normalize_company_name)
    df2["_company_norm"] = df2[COMPANY_COL_2].map(normalize_company_name)

    # Unique company list from memberships (for matching), but keep original label for reference
    df2_companies = (
        df2[[COMPANY_COL_2, "_company_norm"]]
        .drop_duplicates(subset=["_company_norm"])
        .reset_index(drop=True)
    )

    names1 = df1["_company_norm"].fillna("").tolist()
    names2 = df2_companies["_company_norm"].fillna("").tolist()

    # Vectorise & cosine similarity
    vectorizer = TfidfVectorizer(**VECTORIZER_KWARGS)
    X = vectorizer.fit_transform(names1 + names2)
    X1 = X[:len(names1)]
    X2 = X[len(names1):]

    sim = cosine_similarity(X1, X2)
    best_idx = sim.argmax(axis=1)
    best_score = sim.max(axis=1)

    df1["cosine_similarity_best"] = best_score
    df1["matched_company_in_memberships"] = df2_companies.loc[best_idx, COMPANY_COL_2].values
    df1["_matched_company_norm"] = [names2[i] if len(names2) else "" for i in best_idx]
    df1["_match_ok"] = df1["cosine_similarity_best"] >= SIM_THRESHOLD

    # Lookup: membership company norm -> list of (initiative, type)
    membership_lookup = (
        df2.groupby("_company_norm", dropna=False)[[INIT_COL, TYPE_COL]]
        .apply(lambda g: list(map(tuple, g.values.tolist())))
        .to_dict()
    )

    # Determine max memberships for column creation
    counts = []
    for ok, mnorm in zip(df1["_match_ok"].tolist(), df1["_matched_company_norm"].tolist()):
        counts.append(len(membership_lookup.get(mnorm, [])) if ok else 0)

    max_needed = max(counts) if counts else 0
    if MAX_MEMBERSHIPS is not None:
        max_needed = min(max_needed, MAX_MEMBERSHIPS)

    # Create membership/type columns
    for k in range(1, max_needed + 1):
        df1[f"membership_{k}"] = ""
        df1[f"type_{k}"] = ""

    # Also build a clean mapping: company (original string) -> set of initiatives
    company_to_initiatives = {str(c): set() for c in df1[COMPANY_COL_1].tolist()}

    for i in range(len(df1)):
        if not df1.at[i, "_match_ok"]:
            continue

        mnorm = df1.at[i, "_matched_company_norm"]
        items = membership_lookup.get(mnorm, [])
        if MAX_MEMBERSHIPS is not None:
            items = items[:MAX_MEMBERSHIPS]

        # fill membership columns + build initiative set
        for k, (initiative, typ) in enumerate(items, start=1):
            if k <= max_needed:
                df1.at[i, f"membership_{k}"] = initiative
                df1.at[i, f"type_{k}"] = typ
            company_to_initiatives[str(df1.at[i, COMPANY_COL_1])].add(str(initiative))

    # Save matched df1 with memberships (same order)
    df1 = df1.sort_values("_row_id")
    df1_out = df1.drop(columns=["_row_id", "_company_norm", "_matched_company_norm", "_match_ok"])
    df1_out.to_csv(OUT_MATCHED, index=False, encoding="utf-8-sig")

    # ----------------------------
    # Company-level topic flags via organisation_categories.csv
    # ----------------------------
    df3_local = df3.copy()
    for c in TOPIC_COLS:
        df3_local[c] = df3_local[c].map(to_bool)

    init_to_topics = (
        df3_local.set_index(INIT_COL)[TOPIC_COLS]
        .to_dict(orient="index")
    )

    topic_rows = []
    for comp in df1[COMPANY_COL_1].astype(str).tolist():  # preserve original order
        flags = {c: False for c in TOPIC_COLS}
        for init in company_to_initiatives.get(comp, set()):
            topic_info = init_to_topics.get(init)
            if topic_info is None:
                continue
            for c in TOPIC_COLS:
                flags[c] = flags[c] or bool(topic_info.get(c, False))

        topic_rows.append({"company": comp, **flags})

    company_topics = pd.DataFrame(topic_rows)
    company_topics.to_csv(OUT_COMPANY_TOPICS, index=False, encoding="utf-8-sig")

    print("Done.")
    print(f"- Matched + memberships: {OUT_MATCHED}")
    print(f"- Company topic flags: {OUT_COMPANY_TOPICS}")
    print(f"- Similarity threshold: {SIM_THRESHOLD}")

if __name__ == "__main__":
    main()