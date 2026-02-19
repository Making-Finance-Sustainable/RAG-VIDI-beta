## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## Prevalence and co-occurrence plots
## November 2025

##########################################################################
## 1. Dependencies
##########################################################################
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import numpy as np

##########################################################################
## 2. Load CSV and prepare data
##########################################################################

## Data
csv_path = "data/investment_reports_topics.csv"

df = pd.read_csv(csv_path)

## Required columns
if 'annual_report' not in df.columns:
    raise ValueError(f"{csv_path} must contain a 'annual_report' column.")

## Infer topic columns
topic_cols = [c for c in df.columns if c.endswith('_present')]
if len(topic_cols) == 0:
    raise ValueError("No topic columns found. Expected columns ending with '_present'.")

## Treat blank strings as NaN
df[topic_cols] = df[topic_cols].replace(r'^\s*$', np.nan, regex=True)

## Drop missing rows
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
    raise ValueError("The input CSV has no rows. Nothing to plot.")

## Labels for topics
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
## 3. Topic prevalence (share of documents mentioning each topic)
##########################################################################

## Prevalence as proportion of documents where topic == True
prevalence = df[topic_cols].mean().sort_values(ascending=False)

## Reorder topic columns by prevalence for consistent plotting
ordered_topics = prevalence.index.tolist()
prevalence = prevalence.loc[ordered_topics]

## Corresponding labels in the same order
ordered_labels = [topic_label_map.get(col, col) for col in ordered_topics]

##########################################################################
## 4. Topic co-occurrence matrix
##########################################################################

## Co-occurrence: proportion of documents where topic i and j are both present
## Using matrix multiplication on {0,1} representation
X = df[ordered_topics].astype(int)
coocc_counts = X.T.dot(X)              ## Counts of joint occurrences
coocc_matrix = coocc_counts / n_docs   ## Convert to proportions

##########################################################################
## 5. Topic prevalence bar chart
##########################################################################

## Pastel palette
pastel_palette = sns.color_palette("pastel", n_colors=len(ordered_topics))
topic_colors = pastel_palette

fig1, ax1 = plt.subplots(figsize=(10, 6))

x_pos = np.arange(len(ordered_topics))
ax1.bar(x_pos, prevalence.values, color=topic_colors, edgecolor='none')

ax1.set_xticks(x_pos)
ax1.set_xticklabels(ordered_labels, rotation=45, ha='right', fontsize=9)
ax1.set_ylabel("Share of documents", fontsize=11)
ax1.set_title("Topic prevalence across annual reports", fontsize=14, pad=20) 
## Pad is for distance between title and plot

## Remove spines
for spine in ['top', 'right']:
    ax1.spines[spine].set_visible(False)

ax1.set_ylim(0, 1.0)
ax1.tick_params(axis='y', length=0)

plt.tight_layout()

##########################################################################
## 6. Topic co-occurrence heatmap
##########################################################################

fig2, ax2 = plt.subplots(figsize=(8, 7))

## Heatmap of co-occurrence proportions
im = ax2.imshow(
    coocc_matrix.values,
    cmap="YlGnBu", ## Pastel-ish alternative to viridis
    vmin=0,
    vmax=1
)

ax2.set_xticks(np.arange(len(ordered_topics)))
ax2.set_yticks(np.arange(len(ordered_topics)))
ax2.set_xticklabels(ordered_labels, rotation=45, ha='right', fontsize=9)
ax2.set_yticklabels(ordered_labels, fontsize=9)

ax2.set_title("Topic co-occurrence - share of documents", fontsize=14, pad=20)
## Pad is for distance between title and plot

cbar = fig2.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
cbar.ax.set_ylabel("Proportion of documents", rotation=90, va="center")

for spine in ['top', 'right', 'left', 'bottom']:
    ax2.spines[spine].set_visible(False)

ax2.tick_params(axis='both', length=0)

plt.tight_layout()

##########################################################################
## 7. Save figures
##########################################################################

os.makedirs("docs/plots", exist_ok=True)

prev_output = "docs/plots/topic_prevalence"
coocc_output = "docs/plots/topic_cooccurrence"

fig1.savefig(f"{prev_output}.png", dpi=300, bbox_inches='tight', transparent=True)
## fig1.savefig(f"{prev_output}.pdf", dpi=300, bbox_inches='tight')

fig2.savefig(f"{coocc_output}.png", dpi=300, bbox_inches='tight', transparent=True)
## fig2.savefig(f"{coocc_output}.pdf", dpi=300, bbox_inches='tight')

print("\nTopic prevalence bar chart saved.")
print("Topic co-occurrence heatmap saved.")
## plt.show()
