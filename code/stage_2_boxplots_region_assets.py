## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## Boxplots by region and assets quartiles
## February 2026

##########################################################################
## 1. Dependencies
##########################################################################
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

np.random.seed(42)

##########################################################################
## 2. Load CSV and prepare data
##########################################################################

## Data
csv_path = "data/investment_reports_topics.csv"

df = pd.read_csv(csv_path)

required_cols = ["annual_report", "country", "assets"]
missing_required = [c for c in required_cols if c not in df.columns]
if missing_required:
    raise ValueError(
        f"{csv_path} is missing required column(s): {missing_required}. "
        f"Found columns: {list(df.columns)}"
    )

topic_cols = [c for c in df.columns if c.endswith("_present")]
if len(topic_cols) == 0:
    raise ValueError("No topic columns found. Expected columns ending with '_present'.")

df[topic_cols] = df[topic_cols].replace(r"^\s*$", np.nan, regex=True)
df = df.dropna(subset=topic_cols, how="all").copy()

for col in topic_cols:
    col_upper = df[col].astype(str).str.upper().str.strip()
    df[col] = col_upper.map({
        "TRUE": True, "FALSE": False,
        "1": True, "0": False,
        "YES": True, "NO": False
    }).fillna(False).astype(bool)

n_docs = len(df)
if n_docs == 0:
    raise ValueError("The input CSV has no usable rows after cleaning. Nothing to plot.")

df["country"] = df["country"].astype(str).str.strip()
df["assets"] = pd.to_numeric(df["assets"], errors="coerce")

##########################################################################
## 3. Regions (merge North America + Latin America -> Americas)
##########################################################################

country_to_region = {
    ## Europe
    "Norway": "Europe", "Netherlands": "Europe", "France": "Europe", "Germany": "Europe",
    "Sweden": "Europe", "Denmark": "Europe", "UK": "Europe", "Luxembourg": "Europe",
    "Finland": "Europe", "Switzerland": "Europe", "Austria": "Europe", "Portugal": "Europe",
    "Italy": "Europe", "Ireland": "Europe", "Belgium": "Europe", "Iceland": "Europe",

    ## Americas (merged)
    "USA": "Americas", "Canada": "Americas", "Mexico": "Americas",
    "Chile": "Americas", "Colombia": "Americas", "Brazil": "Americas",

    ## Middle East
    "UAE": "Middle East", "Saudi Arabia": "Middle East", "Kuwait": "Middle East",
    "Qatar": "Middle East", "Iran": "Middle East", "Israel": "Middle East",

    ## Asia-Pacific
    "Singapore": "Asia-Pacific", "Japan": "Asia-Pacific", "China": "Asia-Pacific",
    "South Korea": "Asia-Pacific", "Hong Kong": "Asia-Pacific", "Malaysia": "Asia-Pacific",
    "Australia": "Asia-Pacific", "Taiwan": "Asia-Pacific", "India": "Asia-Pacific",
    "Vietnam": "Asia-Pacific", "Philippines": "Asia-Pacific", "Thailand": "Asia-Pacific",
    "Brunei": "Asia-Pacific", "New Zealand": "Asia-Pacific",

    ## Africa
    "South Africa": "Africa", "Libya": "Africa",

    ## Eurasia / Central Asia
    "Turkey": "Eurasia", "Russia": "Eurasia", "Kazakhstan": "Eurasia", "Azerbaijan": "Eurasia",
}

df["region"] = df["country"].map(country_to_region).fillna("Other/Unknown")

##########################################################################
## 4. Assets quartiles
##########################################################################

assets_non_missing = df["assets"].dropna()
if assets_non_missing.nunique() < 4:
    raise ValueError(
        "Assets does not have enough distinct non-missing values to form quartiles (need >= 4)."
    )

quartile_order = ["Q1 (low)", "Q2", "Q3", "Q4 (high)"]
df["assets_quartile"] = pd.qcut(df["assets"], q=4, labels=quartile_order)

##########################################################################
## 5. Derived variables
##########################################################################

df["topic_count"] = df[topic_cols].sum(axis=1).astype(int)

topic_label_map = {
    "sustainable_development_present":     "Sustainable development",
    "responsible_investment_esg_present":  "Responsible investment ESG",
    "green_growth_present":                "Green growth",
    "net_zero_present":                    "Net zero",
    "decarbonization_present":             "Decarbonisation",
    "transition_finance_present":          "Transition finance",
    "conservation_finance_present":        "Conservation finance"
}

##########################################################################
## 6. Plot helper: boxplot ONLY (no scatter points)
##########################################################################

def boxplot_only(
    plot_df: pd.DataFrame,
    x: str,
    y: str,
    order: list,
    palette: dict,
    title: str,
    save_prefix: str,
    figsize=(10, 6),
) -> None:
    plt.figure(figsize=figsize)

    ax = sns.boxplot(
        data=plot_df,
        x=x, y=y,
        hue=x,                 # keep consistent with your earlier structure
        palette=palette,
        order=order,
        hue_order=order,
        dodge=False,
        showfliers=False,
        width=0.55,
        legend=False,
        linewidth=1,
    )

    if ax.get_legend() is not None:
        ax.get_legend().remove()

    ax.set_title(title, fontsize=14, pad=20)
    ax.set_xlabel("")
    ax.set_ylabel("Number of topics mentioned", fontsize=11)
    ax.tick_params(axis="x", rotation=0)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", length=0)

    plt.tight_layout()

    for ext in ("png",):  # add "pdf" if needed
        plt.savefig(
            f"{save_prefix}.{ext}",
            dpi=300,
            bbox_inches="tight",
            transparent=True,
        )
    plt.close()

##########################################################################
## 7. Create plots
##########################################################################

sns.set_style("white")

os.makedirs("docs/plots", exist_ok=True)
os.makedirs("docs/descriptives", exist_ok=True)

## Region palette (pastel dict)
region_order = sorted(df["region"].unique().tolist())
region_colors = sns.color_palette("pastel", n_colors=len(region_order))
region_palette = {k: region_colors[i] for i, k in enumerate(region_order)}

## Quartile palette (pastel dict)
quartile_colors = sns.color_palette("pastel", n_colors=len(quartile_order))
quartile_palette = {k: quartile_colors[i] for i, k in enumerate(quartile_order)}

## Plot 1: by region
boxplot_only(
    plot_df=df,
    x="region",
    y="topic_count",
    order=region_order,
    palette=region_palette,
    title="Topic count across annual reports by region",
    save_prefix="docs/plots/topic_count_boxplot_by_region",
    figsize=(10, 6),
)

## Plot 2: by assets quartile
boxplot_only(
    plot_df=df.dropna(subset=["assets_quartile"]),
    x="assets_quartile",
    y="topic_count",
    order=quartile_order,
    palette=quartile_palette,
    title="Topic count across annual reports by assets quartile",
    save_prefix="docs/plots/topic_count_boxplot_by_assets_quartile",
    figsize=(10, 6),
)

print("\nPlots saved:")
print(" - docs/plots/topic_count_boxplot_by_region.png")
print(" - docs/plots/topic_count_boxplot_by_assets_quartile.png")

##########################################################################
## 8. TXT descriptives (overall + by region + by assets quartile)
##########################################################################

def prevalence_table(dataframe: pd.DataFrame, topics: list) -> pd.Series:
    return dataframe[topics].mean().sort_values(ascending=False)

def describe_topic_count(series: pd.Series) -> dict:
    return {
        "n": int(series.notna().sum()),
        "mean": float(series.mean()),
        "sd": float(series.std(ddof=1)),
        "min": int(series.min()),
        "p25": float(series.quantile(0.25)),
        "median": float(series.median()),
        "p75": float(series.quantile(0.75)),
        "max": int(series.max()),
    }

txt_path = "results/topic_distributions_by_region_and_assets.txt"

with open(txt_path, "w", encoding="utf-8") as f:
    f.write("Making Finance Sustainable VIDI Project\n")
    f.write("Descriptives: topics overall, by region, and by assets quartiles\n")
    f.write(f"Source file: {csv_path}\n")
    f.write(f"Documents (after cleaning): {n_docs}\n\n")

    f.write("=== Overall topic prevalence (share of documents) ===\n")
    overall_prev = prevalence_table(df, topic_cols)
    for col, val in overall_prev.items():
        f.write(f"{topic_label_map.get(col, col)}: {val:.3f}\n")

    f.write("\n=== Overall topic_count descriptives (number of topics per report) ===\n")
    d = describe_topic_count(df["topic_count"])
    f.write(
        f"n={d['n']}, mean={d['mean']:.3f}, sd={d['sd']:.3f}, "
        f"min={d['min']}, p25={d['p25']:.3f}, median={d['median']:.3f}, "
        f"p75={d['p75']:.3f}, max={d['max']}\n"
    )

    f.write("\n\n=== By region ===\n")
    for r in region_order:
        sub = df[df["region"] == r].copy()
        f.write(f"\n-- Region: {r} (n={len(sub)}) --\n")

        d = describe_topic_count(sub["topic_count"])
        f.write(
            f"topic_count: n={d['n']}, mean={d['mean']:.3f}, sd={d['sd']:.3f}, "
            f"min={d['min']}, p25={d['p25']:.3f}, median={d['median']:.3f}, "
            f"p75={d['p75']:.3f}, max={d['max']}\n"
        )

        f.write("topic prevalence:\n")
        prev = prevalence_table(sub, topic_cols)
        for col, val in prev.items():
            f.write(f"  {topic_label_map.get(col, col)}: {val:.3f}\n")

    f.write("\n\n=== By assets quartile ===\n")
    sub_assets = df.dropna(subset=["assets_quartile"]).copy()

    for q in quartile_order:
        sub = sub_assets[sub_assets["assets_quartile"] == q].copy()
        f.write(f"\n-- Assets: {q} (n={len(sub)}) --\n")

        d = describe_topic_count(sub["topic_count"])
        f.write(
            f"topic_count: n={d['n']}, mean={d['mean']:.3f}, sd={d['sd']:.3f}, "
            f"min={d['min']}, p25={d['p25']:.3f}, median={d['median']:.3f}, "
            f"p75={d['p75']:.3f}, max={d['max']}\n"
        )

        f.write("topic prevalence:\n")
        prev = prevalence_table(sub, topic_cols)
        for col, val in prev.items():
            f.write(f"  {topic_label_map.get(col, col)}: {val:.3f}\n")

print(f"\nDescriptives TXT saved: {txt_path}")