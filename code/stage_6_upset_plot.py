## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## Sustainable-finance repertoire analysis - UpSet-style plot
## November 2025

##########################################################################
## 1. Dependencies
##########################################################################

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.gridspec import GridSpec

##########################################################################
## 2. Load CSV and prepare data
##########################################################################

## Data
csv_path = "data/tidy/reports_topics_validation.csv"

df = pd.read_csv(csv_path)

## Required columns
if 'annual_report' not in df.columns:
    raise ValueError(f"{csv_path} must contain an 'annual_report' column.")

## Infer topic columns
topic_cols = [c for c in df.columns if c.endswith('_present')]
if len(topic_cols) == 0:
    raise ValueError("No topic columns found. Expected columns ending with '_present'.")

## Treat blank strings as NaN
df[topic_cols] = df[topic_cols].replace(r'^\s*$', np.nan, regex=True)

## Drop rows with all topic columns missing
df = df.dropna(subset=topic_cols, how='all').copy()

## Convert topic columns to booleans in a robust way
for col in topic_cols:
    col_upper = df[col].astype(str).str.upper()
    df[col] = col_upper.map({
        'TRUE': True,
        'FALSE': False,
        '1': True,
        '0': False
    }).fillna(False).astype(bool)

n_docs = len(df)
if n_docs == 0:
    raise ValueError("The input CSV has no valid rows. Nothing to plot.")

##########################################################################
## 3. Labels and topic ordering
##########################################################################

topic_label_map = {
    "sustainable_development_present":     "Sustainable development",
    "responsible_investment_esg_present":  "Responsible investment/ESG",
    "green_growth_present":                "Green growth",
    "net_zero_present":                    "Net-zero",
    "decarbonization_present":             "Decarbonisation",
    "transition_finance_present":          "Transition finance",
    "conservation_finance_present":        "Conservation finance"
}

## Short labels for the UpSet matrix
topic_short_label_map = {
    "sustainable_development_present":     "Sustainable\ndevelopment",
    "responsible_investment_esg_present":  "Responsible\ninvestment/ESG",
    "green_growth_present":                "Green\ngrowth",
    "net_zero_present":                    "Net-zero",
    "decarbonization_present":             "Decarbonisation",
    "transition_finance_present":          "Transition\nfinance",
    "conservation_finance_present":        "Conservation\nfinance"
}

## Order topics by prevalence, as in the previous plots
prevalence = df[topic_cols].mean().sort_values(ascending=False)
ordered_topics = prevalence.index.tolist()
ordered_labels = [topic_label_map.get(col, col) for col in ordered_topics]
ordered_short_labels = [topic_short_label_map.get(col, col) for col in ordered_topics]

##########################################################################
## 4. Build repertoire combinations
##########################################################################

## Number of topics per report
df["topic_count"] = df[ordered_topics].sum(axis=1)

## Combination key as tuple of booleans in ordered topic order
df["combination_key"] = df[ordered_topics].apply(lambda row: tuple(row.values), axis=1)

## Count combinations
combo_counts = (
    df.groupby("combination_key")
      .size()
      .reset_index(name="n")
      .sort_values("n", ascending=False)
      .reset_index(drop=True)
)

combo_counts["share"] = combo_counts["n"] / n_docs

## Add readable labels and topic-count information
def combination_label(key, topics, label_map):
    present_topics = [
        label_map.get(topic, topic)
        for topic, is_present in zip(topics, key)
        if is_present
    ]
    if len(present_topics) == 0:
        return "No detected topics"
    return " + ".join(present_topics)

combo_counts["combination_label"] = combo_counts["combination_key"].apply(
    lambda x: combination_label(x, ordered_topics, topic_label_map)
)

combo_counts["topic_count"] = combo_counts["combination_key"].apply(sum)

##########################################################################
## 5. Save full combination table for inspection/reporting
##########################################################################

os.makedirs("results", exist_ok=True)

combo_output = combo_counts.copy()

for i, topic in enumerate(ordered_topics):
    combo_output[topic] = combo_output["combination_key"].apply(lambda x: x[i])

combo_output = combo_output[
    ["combination_label", "n", "share", "topic_count"] + ordered_topics
]

combo_output.to_csv("results/topic_repertoire_combinations.csv", index=False)

##########################################################################
## 6. Select combinations to plot
##########################################################################

## Number of combinations to display
top_n = 15

## Exclude the no-topic combination from the plotted combinations
include_empty_combination = False

plot_combos = combo_counts.copy()

if not include_empty_combination:
    plot_combos = plot_combos[plot_combos["topic_count"] > 0].copy()

plot_combos = plot_combos.head(top_n).reset_index(drop=True)

if len(plot_combos) == 0:
    raise ValueError("No positive topic combinations available for plotting.")

##########################################################################
## 7. UpSet-style plot
##########################################################################

## Palette close to your previous pastel style
pastel_palette = sns.color_palette("pastel", n_colors=8)

bar_color = pastel_palette[0]
set_size_color = pastel_palette[2]
dot_color = "#2F2F2F"
empty_dot_color = "#D9D9D9"
line_color = "#2F2F2F"
grid_color = "#F2F2F2"

## Prepare matrix
combination_matrix = np.array(plot_combos["combination_key"].tolist()).astype(bool)
combination_sizes = plot_combos["n"].values
combination_shares = plot_combos["share"].values

set_sizes = df[ordered_topics].sum().values
set_shares = set_sizes / n_docs

x_pos = np.arange(len(plot_combos))
y_pos = np.arange(len(ordered_topics))

## Figure
## Wider figure and larger left panel to give more space to topic labels
fig = plt.figure(figsize=(13.5, 8.5))

gs = GridSpec(
    nrows=2,
    ncols=2,
    width_ratios=[2.3, 5.5],
    height_ratios=[3.0, 2.4],
    hspace=0.05,
    wspace=0.08
)

ax_empty = fig.add_subplot(gs[0, 0])
ax_bar = fig.add_subplot(gs[0, 1])
ax_set = fig.add_subplot(gs[1, 0])
ax_matrix = fig.add_subplot(gs[1, 1])

##########################################################################
## 7.1 Top bar chart: combination sizes
##########################################################################

ax_bar.bar(
    x_pos,
    combination_sizes,
    color=bar_color,
    edgecolor='none'
)

ax_bar.set_ylabel("Number of reports", fontsize=11)
## ax_bar.set_title(
    ## "Most common sustainable-finance reporting repertoires",
    ## fontsize=14,
    ## pad=20
## )

## Add percentage labels above bars
for x, n, share in zip(x_pos, combination_sizes, combination_shares):
    ax_bar.text(
        x,
        n + max(combination_sizes) * 0.025,
        f"{share:.1%}",
        ha="center",
        va="bottom",
        fontsize=8,
        rotation=0
    )

ax_bar.set_xlim(-0.5, len(plot_combos) - 0.5)
ax_bar.set_ylim(0, max(combination_sizes) * 1.18)
ax_bar.set_xticks([])

for spine in ['top', 'right']:
    ax_bar.spines[spine].set_visible(False)

ax_bar.tick_params(axis='y', length=0)
ax_bar.grid(axis='y', color=grid_color, linewidth=0.8)

##########################################################################
## 7.2 Matrix: topic membership in each combination
##########################################################################

## Background alternating bands
for y in y_pos:
    if y % 2 == 0:
        ax_matrix.axhspan(y - 0.5, y + 0.5, color=grid_color, zorder=0)

## Empty dots
for x in x_pos:
    ax_matrix.scatter(
        [x] * len(ordered_topics),
        y_pos,
        s=55,
        color=empty_dot_color,
        zorder=2
    )

## Filled dots and connecting lines
for x, row in zip(x_pos, combination_matrix):
    included_y = y_pos[row]

    if len(included_y) > 0:
        if len(included_y) > 1:
            ax_matrix.plot(
                [x, x],
                [included_y.min(), included_y.max()],
                color=line_color,
                linewidth=1.6,
                zorder=3
            )

        ax_matrix.scatter(
            [x] * len(included_y),
            included_y,
            s=65,
            color=dot_color,
            zorder=4
        )

ax_matrix.set_xlim(-0.5, len(plot_combos) - 0.5)
ax_matrix.set_ylim(len(ordered_topics) - 0.5, -0.5)

ax_matrix.set_yticks(y_pos)
ax_matrix.set_yticklabels([])

ax_matrix.set_xticks(x_pos)
ax_matrix.set_xticklabels(
    [str(i + 1) for i in x_pos],
    fontsize=9
)

ax_matrix.set_xlabel("Repertoire combination rank", fontsize=11, labelpad=10)

for spine in ['top', 'right', 'left', 'bottom']:
    ax_matrix.spines[spine].set_visible(False)

ax_matrix.tick_params(axis='both', length=0)

##########################################################################
## 7.3 Left bar chart: topic set sizes
##########################################################################

ax_set.barh(
    y_pos,
    set_sizes,
    color=set_size_color,
    edgecolor='none'
)

ax_set.set_yticks(y_pos)
ax_set.set_yticklabels(ordered_short_labels, fontsize=9)
ax_set.tick_params(axis='y', pad=35)

ax_set.invert_yaxis()
ax_set.invert_xaxis()

ax_set.set_xlabel("Reports", fontsize=10)

for y, n, share in zip(y_pos, set_sizes, set_shares):
    ax_set.text(
        n + max(set_sizes) * 0.03,
        y,
        f"{share:.1%}",
        ha="right",
        va="center",
        fontsize=8
    )

for spine in ['top', 'right', 'left']:
    ax_set.spines[spine].set_visible(False)

ax_set.tick_params(axis='both', length=0)
ax_set.grid(axis='x', color=grid_color, linewidth=0.8)

##########################################################################
## 7.4 Empty upper-left panel
##########################################################################

ax_empty.axis("off")

##########################################################################
## 7.5 Caption-like note
##########################################################################

note = (
    f"Note. The plot shows the {len(plot_combos)} most common positive topic "
    f"combinations among {n_docs} annual reports with valid topic indicators. "
    "Reports with no detected sustainable-finance topic are excluded from the "
    "combination ranking shown here. Dots indicate which sustainable-finance "
    "topics are present in each combination. Left bars report topic prevalence; "
    "top bars report combination size."
)

## fig.text(
    ## 0.01,
    ## 0.01,
    ## note,
    ## ha="left",
    ## va="bottom",
    ## fontsize=9,
    ## style="italic",
    ## wrap=True
## )

## Manual spacing instead of tight_layout().
## This avoids: UserWarning: This figure includes Axes that are not compatible with tight_layout.
fig.subplots_adjust(
    left=0.08,
    right=0.98,
    top=0.90,
    bottom=0.13,
    wspace=0.08,
    hspace=0.05
)

##########################################################################
## 8. Save figure
##########################################################################

upset_output = "results/topic_repertoires_upset"

fig.savefig(f"{upset_output}.png", dpi=300, bbox_inches='tight', transparent=True)
fig.savefig(f"{upset_output}.pdf", dpi=300, bbox_inches='tight')

print("\nSustainable-finance repertoire UpSet-style plot saved.")
print(f"PNG: {upset_output}.png")
print(f"PDF: {upset_output}.pdf")
print("Combination table saved: results/topic_repertoire_combinations.csv")

##########################################################################
## 9. Print top combinations for quick inspection
##########################################################################

print(f"\nNumber of valid annual reports used as denominator: {n_docs}")

print("\nTop positive repertoire combinations:")
print(
    combo_output[combo_output["topic_count"] > 0]
    .head(top_n)
    [["combination_label", "n", "share", "topic_count"]]
    .to_string(index=False)
)

## plt.show()